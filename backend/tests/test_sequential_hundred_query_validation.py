from eval.scripts.run_sequential_hundred_query_validation import build_cases


def test_sequential_hundred_query_validation_defines_one_hundred_unique_multitable_cases() -> None:
    cases = build_cases()

    assert len(cases) == 100
    assert len({case.id for case in cases}) == 100
    assert all(len(case.query_plan["entities"]) >= 2 for case in cases)
