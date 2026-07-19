from eval.scripts.generate_comprehensive_agent_cases import CATEGORY_QUOTAS, build_cases, validate_cases


def test_comprehensive_agent_cases_have_expected_size_and_category_coverage() -> None:
    cases = build_cases()

    assert len(cases) == 200
    assert {category: sum(case["category"] == category for case in cases) for category in CATEGORY_QUOTAS} == CATEGORY_QUOTAS


def test_comprehensive_agent_cases_are_schema_valid() -> None:
    validate_cases(build_cases())


def test_comprehensive_agent_cases_do_not_send_cancel_or_non_data_routes_to_database() -> None:
    cases = build_cases()

    cancel_case = next(case for case in cases if case["question"] == "取消")
    assert cancel_case["expected_route"] == "cancelled"
    assert cancel_case["should_access_database"] is False
    assert cancel_case["should_generate_sql"] is False
    assert all(
        case["should_access_database"] is False
        for case in cases
        if case["category"] in {"general_chat", "explain_result", "unsupported", "api_boundary"}
    )
    failure_cases = [case for case in cases if case["category"] == "failure_safety"]
    assert len(failure_cases) == 5
    assert all(case["expected_http_status"] == 503 for case in failure_cases)
    assert all(case["should_access_database"] is False for case in failure_cases)
