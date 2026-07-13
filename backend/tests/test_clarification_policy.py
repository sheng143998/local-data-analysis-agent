from backend.app.tools.clarification_policy import ClarificationPolicy, apply_clarification_policy
from backend.app.tools.question_intent_parser import ParsedQuestionIntent


def test_unknown_but_explicit_semantic_metric_executes() -> None:
    intent = ParsedQuestionIntent(original_question="物流及时率是多少", normalized_question="物流及时率是多少", semantic_metrics=["物流及时率"], confidence=0.1)
    decision = ClarificationPolicy().decide(intent)

    assert decision.action == "execute"


def test_missing_business_target_clarifies_with_structured_reason() -> None:
    intent = ParsedQuestionIntent(original_question="看看最近情况", normalized_question="看看最近情况")
    resolved = apply_clarification_policy(intent)

    assert resolved.needs_clarification is True
    assert resolved.clarification_reason == "missing_business_target"


def test_contract_conflict_clarifies_without_resolver_owned_text() -> None:
    intent = ParsedQuestionIntent(original_question="用户数", normalized_question="用户数", semantic_conflicts=["registered_users", "ordering_users"])
    resolved = apply_clarification_policy(intent)

    assert resolved.needs_clarification is True
    assert resolved.clarification_reason == "multiple_semantic_contracts"
