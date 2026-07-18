from eval.scripts.run_eval import (
    EvaluationConfigurationError,
    EvalCase,
    _build_run_trace_summary,
    _extract_eval_run_trace,
    _fetch_run_trace_summary,
    _find_latest_run_id,
    authenticate_evaluation_client,
    build_batch_metadata,
    load_cases,
    load_database_ground_truth_cases,
    load_regression_cases,
    run_cases,
    select_case_batch,
    summarize_results,
    _performance_summary,
)
from pathlib import Path


class _FakeLoginResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


class _FakeLoginClient:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.requests: list[tuple[str, dict]] = []

    def post(self, path: str, json: dict):  # type: ignore[no-untyped-def]
        self.requests.append((path, json))
        return _FakeLoginResponse(self.status_code)


def test_load_standard_questions_contains_twenty_cases() -> None:
    cases = load_cases()

    assert len(cases) == 20
    assert cases[0].id == "basic_001"
    assert cases[-1].id == "marketing_020"


def test_load_regression_questions_contains_forbidden_assertions() -> None:
    cases = load_regression_cases()

    assert len(cases) == 5
    assert cases[0].id == "regression_001"
    assert "avg_order_value" in cases[0].expected_keywords
    assert "AVG(payments.amount)" in cases[0].forbidden_keywords


def test_load_database_ground_truth_questions_contains_fifty_cases() -> None:
    cases = load_database_ground_truth_cases()

    assert len(cases) == 50
    assert cases[0].expected_answer == "99,441"
    assert cases[-1].result_match_mode == "skip"


def test_select_case_batch_uses_stable_non_overlapping_ranges() -> None:
    cases = [
        EvalCase(str(index), "分批", f"问题 {index}", [], [])
        for index in range(5)
    ]

    first_batch = select_case_batch(cases, start=0, limit=2)
    second_batch = select_case_batch(cases, start=2, limit=2)
    last_batch = select_case_batch(cases, start=4, limit=2)

    assert [case.id for case in first_batch] == ["0", "1"]
    assert [case.id for case in second_batch] == ["2", "3"]
    assert [case.id for case in last_batch] == ["4"]
    assert {case.id for case in first_batch}.isdisjoint(case.id for case in second_batch)


def test_select_case_batch_rejects_invalid_or_out_of_range_selection() -> None:
    cases = [EvalCase("0", "分批", "问题", [], [])]

    for kwargs in ({"start": -1}, {"limit": 0}, {"start": 1}):
        try:
            select_case_batch(cases, **kwargs)
        except EvaluationConfigurationError:
            continue
        raise AssertionError("非法分段参数必须在执行模型前明确阻断")


def test_build_batch_metadata_marks_partial_report_scope() -> None:
    all_cases = [
        EvalCase("case_1", "分批", "问题 1", [], []),
        EvalCase("case_2", "分批", "问题 2", [], []),
        EvalCase("case_3", "分批", "问题 3", [], []),
    ]

    metadata = build_batch_metadata(
        Path("eval/datasets/database_ground_truth_questions.jsonl"),
        all_cases,
        all_cases[1:3],
        start=1,
        limit=2,
    )

    assert metadata == {
        "path": "eval/datasets/database_ground_truth_questions.jsonl",
        "total_case_count": 3,
        "selected_start": 1,
        "selected_limit": 2,
        "selected_case_count": 2,
        "selected_case_ids": ["case_2", "case_3"],
        "is_complete_dataset": False,
    }


def test_authenticate_evaluation_client_requires_explicit_credentials() -> None:
    try:
        authenticate_evaluation_client(
            _FakeLoginClient(),  # type: ignore[arg-type]
            auth_required=True,
            environment={},
        )
    except EvaluationConfigurationError as exc:
        assert "EVAL_AUTH_EMAIL" in str(exc)
    else:
        raise AssertionError("缺少评测账号时应明确阻断")


def test_authenticate_evaluation_client_logs_in_with_explicit_credentials() -> None:
    client = _FakeLoginClient()

    authenticate_evaluation_client(
        client,  # type: ignore[arg-type]
        auth_required=True,
        environment={"EVAL_AUTH_EMAIL": "eval@example.com", "EVAL_AUTH_PASSWORD": "safe-password"},
    )

    assert client.requests == [
        ("/api/auth/login", {"email": "eval@example.com", "password": "safe-password"})
    ]


def test_run_cases_and_summary_collect_eval_metrics() -> None:
    cases = [
        EvalCase(
            id="case_1",
            category="基础查询",
            question="最近 7 天销售额是多少？",
            expected_tables=["orders"],
            expected_keywords=["SELECT"],
        ),
        EvalCase(
            id="case_2",
            category="基础查询",
            question="坏问题",
            expected_tables=["orders"],
            expected_keywords=["SELECT"],
        ),
    ]

    def fake_analyze(question: str):
        if question == "坏问题":
            return 500, {"summary": "failed"}
        return 200, {
            "path": "fast_path",
            "sql": "SELECT o.id FROM orders o LIMIT 10",
            "source": {"security": "只读 SELECT，已通过 SQL Guard", "returnedRows": 1},
            "trace": {},
            "_eval_run_id": "11111111-1111-1111-1111-111111111111",
            "_eval_run_detail_path": "/api/runs/11111111-1111-1111-1111-111111111111",
            "_eval_run_trace_summary": {
                "context_tables": ["orders"],
                "generation_path": "model_generate",
            },
        }

    results = run_cases(cases, fake_analyze)
    report = summarize_results(results)

    assert report["total"] == 2
    assert report["success_count"] == 1
    assert report["strict_success_count"] == 1
    assert report["execution_success_rate"] == 0.5
    assert report["strict_success_rate"] == 0.5
    assert report["sql_generation_success_rate"] == 0.5
    assert report["table_match_rate"] == 0.5
    assert report["keyword_match_rate"] == 0.5
    assert report["forbidden_match_rate"] == 1
    assert report["memory_hit_rate"] == 0.5
    assert report["reuse_success_rate"] == 0.5
    assert report["path_counts"] == {"fast_path": 1, "": 1}
    assert len(report["failures"]) == 1
    assert report["cases"][0]["strict_ok"] is True
    assert report["cases"][0]["run_id"] == "11111111-1111-1111-1111-111111111111"
    assert (
        report["cases"][0]["run_detail_path"]
        == "/api/runs/11111111-1111-1111-1111-111111111111"
    )
    assert report["cases"][0]["run_trace_summary"]["context_tables"] == ["orders"]
    assert report["cases"][1]["strict_ok"] is False


def test_run_cases_compares_structured_rows_against_ground_truth_tokens() -> None:
    case = EvalCase(
        id="ground_truth_001",
        category="真实库基线",
        question="各状态数量",
        expected_tables=["orders"],
        expected_keywords=["SELECT"],
        expected_answer="delivered 96,478；shipped 1,107",
    )

    results = run_cases(
        [case],
        lambda _: (
            200,
            {
                "path": "cold_path",
                "sql": "SELECT status, COUNT(*) FROM orders GROUP BY status",
                "rows": [
                    {"status": "delivered", "order_count": 96478},
                    {"status": "shipped", "order_count": 1107},
                ],
                "source": {"security": "只读 SELECT，已通过 SQL Guard", "returnedRows": 2},
            },
        ),
    )
    report = summarize_results(results)

    assert results[0].answer_match is True
    assert results[0].strict_ok is True
    assert report["answer_checked_count"] == 1
    assert report["answer_match_rate"] == 1


def test_summary_separates_execution_success_from_assertion_match() -> None:
    cases = [
        EvalCase(
            id="case_1",
            category="漏斗与营销",
            question="哪些优惠券核销率最高？",
            expected_tables=["coupons"],
            expected_keywords=["coupon"],
        )
    ]

    def fake_analyze(question: str):
        return 200, {
            "path": "cold_path",
            "sql": "SELECT o.id FROM orders o LIMIT 10",
            "source": {"security": "只读 SELECT，已通过 SQL Guard", "returnedRows": 1},
            "trace": {},
        }

    results = run_cases(cases, fake_analyze)
    report = summarize_results(results)

    assert report["success_count"] == 1
    assert report["strict_success_count"] == 0
    assert report["execution_success_rate"] == 1
    assert report["strict_success_rate"] == 0
    assert report["table_match_rate"] == 0
    assert report["keyword_match_rate"] == 0
    assert report["assertion_failures"][0]["missing_tables"] == ["coupons"]
    assert report["assertion_failure_summary"] == {
        "total": 1,
        "by_missing_table": [{"name": "coupons", "count": 1}],
        "by_forbidden_keyword": [],
        "by_missing_table_context_status": [
            {"name": "coupons", "missing_from_context": 1, "present_in_context": 0}
        ],
        "by_category": [{"name": "漏斗与营销", "count": 1}],
        "by_path": [{"name": "cold_path", "count": 1}],
        "case_ids": ["case_1"],
    }


def test_summary_reports_forbidden_keyword_regression() -> None:
    cases = [
        EvalCase(
            id="regression_1",
            category="聚合口径",
            question="2017年卖了多少钱，平均卖了多少钱",
            expected_tables=["orders", "payments"],
            expected_keywords=["sales_amount"],
            forbidden_keywords=["SUM(o.total_amount) AS sales_amount FROM orders o JOIN payments"],
        )
    ]

    def fake_analyze(question: str):
        return 200, {
            "path": "model_generate",
            "sql": (
                "SELECT SUM(o.total_amount) AS sales_amount FROM orders o "
                "JOIN payments p ON p.order_id = o.id"
            ),
            "source": {"security": "只读 SELECT，已通过 SQL Guard", "returnedRows": 1},
            "trace": {},
            "_eval_run_trace_summary": {"context_tables": ["orders", "payments"]},
        }

    report = summarize_results(run_cases(cases, fake_analyze))

    assert report["success_count"] == 1
    assert report["strict_success_count"] == 0
    assert report["forbidden_match_rate"] == 0
    assert report["assertion_failures"][0]["forbidden_keyword_hits"] == [
        "SUM(o.total_amount) AS sales_amount FROM orders o JOIN payments"
    ]
    assert report["assertion_failure_summary"]["by_forbidden_keyword"] == [
        {"name": "SUM(o.total_amount) AS sales_amount FROM orders o JOIN payments", "count": 1}
    ]


def test_eval_run_trace_extracts_detail_path() -> None:
    assert _extract_eval_run_trace({}) == (None, "", {})
    assert _extract_eval_run_trace({"_eval_run_id": "run-1"}) == (
        "run-1",
        "/api/runs/run-1",
        {},
    )
    assert _extract_eval_run_trace(
        {
            "_eval_run_id": "run-2",
            "_eval_run_detail_path": "/api/runs/run-2",
            "_eval_run_trace_summary": {"context_tables": ["orders"]},
        }
    ) == ("run-2", "/api/runs/run-2", {"context_tables": ["orders"]})


def test_find_latest_run_id_matches_question() -> None:
    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self.payload = payload

        def json(self):
            return self.payload

    class FakeClient:
        def get(self, path):
            assert path == "/api/runs?limit=5"
            return FakeResponse(
                200,
                [
                    {"id": "run-newer", "user_question": "其他问题"},
                    {"id": "run-target", "user_question": "目标问题"},
                ],
            )

    assert _find_latest_run_id(FakeClient(), "目标问题") == "run-target"


def test_build_run_trace_summary_from_tool_calls() -> None:
    summary = _build_run_trace_summary(
        {
            "tool_calls": [
                {
                    "tool_name": "context_builder.build_retrieval_context",
                    "output_payload": {
                        "metric_count": 2,
                        "schema_column_count": 12,
                        "relationship_count": 3,
                        "tables": ["orders", "payments"],
                        "fields_sample": ["orders.id", "payments.order_id"],
                    },
                },
                {
                    "tool_name": "analysis_graph.select_generated_sql",
                    "output_payload": {
                        "generation_path": "model_generate",
                        "warning_count": 1,
                        "warnings": ["模型提示"],
                    },
                },
                {
                    "tool_name": "sql_validation_tools.guard_sql",
                    "output_payload": {
                        "guard_status": "allowed",
                        "warning_count": 0,
                        "warnings": [],
                        "error_count": 0,
                        "errors": [],
                    },
                },
                {
                    "tool_name": "sql_memory_tools.plan_sql_reuse",
                    "output_payload": {
                        "path_type": "cold_path",
                        "reuse_type": "regenerate",
                        "memory_hit": False,
                        "score": 0,
                    },
                },
                {
                    "tool_name": "analysis_graph.pipeline_timings",
                    "output_payload": {
                        "node_timings_ms": {"sql_generation": 12},
                        "total_latency_ms": 30,
                        "slowest_node": {"name": "sql_generation", "latency_ms": 12},
                    },
                },
            ]
        }
    )

    assert summary == {
        "context_tables": ["orders", "payments"],
        "context_fields_sample": ["orders.id", "payments.order_id"],
        "metric_count": 2,
        "schema_column_count": 12,
        "relationship_count": 3,
        "generation_path": "model_generate",
        "generation_warning_count": 1,
        "generation_warnings": ["模型提示"],
        "guard_status": "allowed",
        "guard_warning_count": 0,
        "guard_warnings": [],
        "guard_error_count": 0,
        "guard_errors": [],
        "memory_path_type": "cold_path",
        "memory_reuse_type": "regenerate",
        "memory_hit": False,
        "memory_score": 0,
        "node_timings_ms": {"sql_generation": 12},
        "total_latency_ms": 30,
        "slowest_node": {"name": "sql_generation", "latency_ms": 12},
        "model_route": {},
        "repair_attempts": 0,
    }


def test_fetch_run_trace_summary_reads_run_detail() -> None:
    class FakeResponse:
        status_code = 200

        def json(self):
            return {
                "tool_calls": [
                    {
                        "tool_name": "context_builder.build_retrieval_context",
                        "output_payload": {"tables": ["users"]},
                    }
                ]
            }

    class FakeClient:
        def get(self, path):
            assert path == "/api/runs/run-1"
            return FakeResponse()

    assert _fetch_run_trace_summary(FakeClient(), "run-1")["context_tables"] == ["users"]


def test_summary_groups_assertion_failures_by_table_category_and_path() -> None:
    cases = [
        EvalCase(
            id="user_1",
            category="用户分析",
            question="下单用户数",
            expected_tables=["users", "orders"],
            expected_keywords=["SELECT"],
        ),
        EvalCase(
            id="funnel_1",
            category="漏斗与营销",
            question="访问转化率",
            expected_tables=["traffic_events", "orders"],
            expected_keywords=["SELECT"],
        ),
        EvalCase(
            id="funnel_2",
            category="漏斗与营销",
            question="流量来源转化率",
            expected_tables=["traffic_events"],
            expected_keywords=["SELECT"],
        ),
    ]

    def fake_analyze(question: str):
        if question == "下单用户数":
            sql = "SELECT COUNT(*) FROM orders"
            path = "rewrite_path"
            context_tables = ["users", "orders"]
        elif question == "访问转化率":
            sql = "SELECT COUNT(*) FROM orders"
            path = "rewrite_path"
            context_tables = ["orders"]
        else:
            sql = "SELECT COUNT(*) FROM orders"
            path = "fast_path"
            context_tables = ["orders"]
        return 200, {
            "path": path,
            "sql": sql,
            "source": {"security": "只读 SELECT，已通过 SQL Guard", "returnedRows": 1},
            "trace": {},
            "_eval_run_trace_summary": {"context_tables": context_tables},
        }

    report = summarize_results(run_cases(cases, fake_analyze))

    assert report["assertion_failure_summary"] == {
        "total": 3,
        "by_missing_table": [
            {"name": "traffic_events", "count": 2},
            {"name": "users", "count": 1},
        ],
        "by_forbidden_keyword": [],
        "by_missing_table_context_status": [
            {"name": "traffic_events", "missing_from_context": 2, "present_in_context": 0},
            {"name": "users", "missing_from_context": 0, "present_in_context": 1},
        ],
        "by_category": [
            {"name": "漏斗与营销", "count": 2},
            {"name": "用户分析", "count": 1},
        ],
        "by_path": [
            {"name": "rewrite_path", "count": 2},
            {"name": "fast_path", "count": 1},
        ],
        "case_ids": ["user_1", "funnel_1", "funnel_2"],
    }


def test_performance_summary_separates_graph_and_unattributed_time() -> None:
    results = run_cases(
        [EvalCase("timing", "性能", "问题", [], [])],
        lambda _: (200, {"path": "cold_path", "sql": "SELECT 1", "source": {"security": "SQL Guard", "returnedRows": 1}, "_eval_run_trace_summary": {"node_timings_ms": {"sql_generation": 30, "sql_execution": 20}, "slowest_node": {"name": "sql_generation"}}}),
    )
    summary = _performance_summary(results)

    assert summary["stages_ms"]["graph_known"]["total"] == 50
    assert summary["stages_ms"]["api_total"]["count"] == 1
    assert summary["stages_ms"]["unattributed"]["total"] == 0
    assert summary["slowest_node_counts"] == [{"name": "sql_generation", "count": 1}]
