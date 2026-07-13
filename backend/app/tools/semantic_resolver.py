from dataclasses import dataclass

from backend.app.db.repositories.semantic_contract_repository import SemanticContractRepository
from backend.app.schemas.semantic_contracts import SemanticContract
from backend.app.tools.question_intent_parser import ParsedQuestionIntent


@dataclass(frozen=True)
class SemanticResolution:
    contracts: list[SemanticContract]
    conflicts: list[SemanticContract]


class SemanticResolver:
    """把已审核业务契约绑定到意图，未知概念仍由后续检索和模型处理。"""

    def __init__(self, repository: SemanticContractRepository | None = None) -> None:
        self.repository = repository or SemanticContractRepository()

    def resolve(self, intent: ParsedQuestionIntent) -> SemanticResolution:
        candidates = _candidate_texts(intent)
        matched = [contract for contract in self.repository.list_enabled() if _matches(contract, candidates)]
        unique = _unique_latest(matched)
        conflicts = _conflicts(unique)
        return SemanticResolution(contracts=unique, conflicts=conflicts)


def apply_semantic_resolution(
    intent: ParsedQuestionIntent,
    resolver: SemanticResolver | None = None,
) -> ParsedQuestionIntent:
    resolution = (resolver or SemanticResolver()).resolve(intent)
    payload = [_contract_summary(contract) for contract in resolution.contracts]
    return intent.model_copy(
        update={
            "resolved_contracts": payload,
            "semantic_conflicts": [contract.contract_key for contract in resolution.conflicts],
        }
    )


def _candidate_texts(intent: ParsedQuestionIntent) -> list[str]:
    return [intent.original_question, *intent.semantic_metrics, *intent.semantic_dimensions, *intent.metrics, *intent.dimensions]


def _matches(contract: SemanticContract, candidates: list[str]) -> bool:
    names = [contract.contract_key, contract.display_name, *contract.synonyms]
    return any(_key(name) and _key(name) in _key(candidate) for name in names for candidate in candidates)


def _unique_latest(contracts: list[SemanticContract]) -> list[SemanticContract]:
    latest: dict[str, SemanticContract] = {}
    for contract in contracts:
        previous = latest.get(contract.contract_key)
        if previous is None or contract.version > previous.version:
            latest[contract.contract_key] = contract
    return sorted(latest.values(), key=lambda item: (item.contract_type, item.contract_key))


def _conflicts(contracts: list[SemanticContract]) -> list[SemanticContract]:
    groups: dict[str, list[SemanticContract]] = {}
    for contract in contracts:
        group = str(contract.semantic_config.get("conflict_group") or "")
        if group:
            groups.setdefault(group, []).append(contract)
    return [contract for contracts in groups.values() if len(contracts) > 1 for contract in contracts]


def _contract_summary(contract: SemanticContract) -> dict:
    return {
        "contract_key": contract.contract_key,
        "version": contract.version,
        "contract_type": contract.contract_type,
        "display_name": contract.display_name,
        "source_tables": contract.source_tables,
        "source_fields": contract.source_fields,
        "aggregation": contract.aggregation,
        "time_grain": contract.time_grain,
        "semantic_config": contract.semantic_config,
    }


def _key(value: str) -> str:
    return "".join(str(value).lower().split()).replace("_", "").replace("-", "")
