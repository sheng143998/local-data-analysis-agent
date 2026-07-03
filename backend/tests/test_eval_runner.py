from eval.scripts.run_eval import EvalCase, load_cases, run_cases, summarize_results


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
