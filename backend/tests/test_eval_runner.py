from eval.scripts.run_eval import (
    EvalCase,
    _build_run_trace_summary,
    _extract_eval_run_trace,
    _fetch_run_trace_summary,
    _find_latest_run_id,
    load_cases,
    run_cases,
    summarize_results,
)


def test_load_standard_questions_contains_twenty_cases() -> None:
    cases = load_cases()

    assert len(cases) == 20
    assert cases[0].id == "basic_001"
    assert cases[-1].id == "marketing_020"


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
                "generation_path": "template_render",
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
        "by_missing_table_context_status": [
            {"name": "coupons", "missing_from_context": 1, "present_in_context": 0}
        ],
        "by_category": [{"name": "漏斗与营销", "count": 1}],
        "by_path": [{"name": "cold_path", "count": 1}],
        "case_ids": ["case_1"],
    }


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
