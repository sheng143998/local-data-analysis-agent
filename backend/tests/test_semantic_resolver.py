from backend.app.schemas.semantic_contracts import SemanticContract
from backend.app.tools.question_intent_parser import ParsedQuestionIntent
from backend.app.tools.semantic_resolver import SemanticResolver, apply_semantic_resolution
from backend.app.tools.clarification_policy import apply_clarification_policy


class _Repository:
    def __init__(self, contracts):
        self.contracts = contracts

    def list_enabled(self):
        return self.contracts


def _contract(key: str, label: str, *, synonyms: list[str], config: dict | None = None) -> SemanticContract:
    return SemanticContract(
        contract_key=key, version=1, contract_type="metric", display_name=label,
        business_definition="测试口径", synonyms=synonyms, semantic_config=config or {}, status="enabled",
    )


def test_resolver_binds_unique_contract_without_forcing_clarification() -> None:
    intent = ParsedQuestionIntent(original_question="当前用户总数是多少", normalized_question="当前用户总数是多少", semantic_metrics=["当前用户总数"])
    resolved = apply_semantic_resolution(intent, SemanticResolver(_Repository([_contract("user_total", "用户总数", synonyms=["当前用户总数"])])))

    assert resolved.needs_clarification is False
    assert resolved.resolved_contracts[0]["contract_key"] == "user_total"


def test_resolver_keeps_unknown_clear_concept_open() -> None:
    intent = ParsedQuestionIntent(original_question="物流及时率是多少", normalized_question="物流及时率是多少", semantic_metrics=["物流及时率"])
    resolved = apply_semantic_resolution(intent, SemanticResolver(_Repository([])))

    assert resolved.needs_clarification is False
    assert resolved.resolved_contracts == []


def test_resolver_clarifies_only_contract_conflict() -> None:
    contracts = [
        _contract("registered_users", "注册用户", synonyms=["用户数"], config={"conflict_group": "user_population"}),
        _contract("ordering_users", "下单用户", synonyms=["用户数"], config={"conflict_group": "user_population"}),
    ]
    intent = ParsedQuestionIntent(original_question="用户数是多少", normalized_question="用户数是多少", semantic_metrics=["用户数"])
    resolved = apply_semantic_resolution(intent, SemanticResolver(_Repository(contracts)))

    assert resolved.needs_clarification is False
    assert set(resolved.semantic_conflicts) == {"registered_users", "ordering_users"}
    assert apply_clarification_policy(resolved).clarification_reason == "multiple_semantic_contracts"
