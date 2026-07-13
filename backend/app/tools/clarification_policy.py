from dataclasses import dataclass

from backend.app.tools.question_intent_parser import ParsedQuestionIntent


@dataclass(frozen=True)
class ClarificationDecision:
    action: str
    missing_slots: list[str]
    conflicts: list[str]
    reason_codes: list[str]


class ClarificationPolicy:
    """只依据可解释业务缺口决定是否追问，不使用模型置信度作为规则。"""

    def decide(self, intent: ParsedQuestionIntent) -> ClarificationDecision:
        if intent.semantic_conflicts:
            return ClarificationDecision("clarify", [], intent.semantic_conflicts, ["multiple_semantic_contracts"])
        has_business_target = bool(intent.metrics or intent.semantic_metrics or intent.resolved_contracts)
        if not has_business_target:
            return ClarificationDecision("clarify", ["metrics"], [], ["missing_business_target"])
        return ClarificationDecision("execute", [], [], [])


def apply_clarification_policy(intent: ParsedQuestionIntent) -> ParsedQuestionIntent:
    decision = ClarificationPolicy().decide(intent)
    if decision.action == "execute":
        return intent.model_copy(update={"needs_clarification": False, "clarification_reason": ""})
    clarification = intent.clarification or "请补充你想分析的业务对象或指标，我会据此继续查询。"
    return intent.model_copy(
        update={
            "needs_clarification": True,
            "clarification": clarification,
            "clarification_reason": decision.reason_codes[0],
        }
    )
