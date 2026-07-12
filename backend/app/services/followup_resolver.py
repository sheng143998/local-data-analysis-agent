from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from backend.app.schemas.conversation import PendingClarification
from backend.app.schemas.query_spec import QuerySpec
from backend.app.tools.query_spec import DIMENSION_LABELS, METRIC_LABELS, build_query_spec
from backend.app.tools.question_intent_parser import ParsedQuestionIntent, parse_question_intent


@dataclass(frozen=True)
class FollowupResolution:
    decision: Literal["answer_pending", "new_question", "cancel", "still_pending"]
    intent: ParsedQuestionIntent | None = None
    pending: PendingClarification | None = None


_CANCEL_TOKENS = ("取消", "算了", "不用了", "不问了", "停止")
_REJECT_SUGGESTION_TOKENS = ("不想查询这些", "不想查这些", "不是这些", "不要这些", "换一个", "换个问题")


def resolve_followup(answer: str, pending: PendingClarification) -> FollowupResolution:
    """Resolve a pending clarification by merging structured slots, never raw chat history."""
    normalized = answer.strip()
    if any(token in normalized for token in _CANCEL_TOKENS):
        return FollowupResolution(decision="cancel")

    if any(token in normalized for token in _REJECT_SUGGESTION_TOKENS):
        # 用户否定的是上一轮建议，不代表原始问题已取消。把原问题连同否定语义交回模型重新理解，
        # 避免继续复用已被拒绝的固定澄清文案。
        original_intent = parse_question_intent(
            pending.original_question,
            conversation_context=(
                f"原始问题：{pending.original_question}\n"
                f"此前澄清建议：{pending.clarification}\n"
                f"用户拒绝了此前建议：{normalized}\n"
                "请仅根据原始问题重新识别用户真正要查询的业务语义，不要沿用已被拒绝的建议。"
            ),
        )
        return FollowupResolution(decision="new_question", intent=original_intent)

    answer_intent = parse_question_intent(
        normalized,
        conversation_context=(
            f"原始问题：{pending.original_question}\n"
            f"待补充信息：{'、'.join(pending.missing_slots)}\n"
            f"澄清问题：{pending.clarification}"
        ),
    )
    merged_metrics = _merge(pending.query_spec.metrics, answer_intent.metrics)
    merged_dimensions = _merge(pending.query_spec.dimensions, answer_intent.dimensions)
    existing_semantic_metrics = [str(item) for item in pending.parsed_intent.get("semantic_metrics") or []]
    existing_semantic_dimensions = [str(item) for item in pending.parsed_intent.get("semantic_dimensions") or []]
    merged_semantic_metrics = _merge(existing_semantic_metrics, answer_intent.semantic_metrics)
    merged_semantic_dimensions = _merge(existing_semantic_dimensions, answer_intent.semantic_dimensions)
    merged_time = answer_intent.time_range or pending.query_spec.time_range

    answered_metrics = "metrics" not in pending.missing_slots or bool(merged_metrics or merged_semantic_metrics)
    answered_time = "time_range" not in pending.missing_slots or bool(answer_intent.time_range)
    if answered_metrics and answered_time and (merged_metrics or merged_semantic_metrics):
        canonical_question = _render_canonical_question(
            pending.original_question,
            merged_metrics,
            merged_dimensions,
            merged_time,
        )
        query_spec = build_query_spec(canonical_question, merged_metrics, merged_dimensions, merged_time)
        intent = answer_intent.model_copy(
            update={
                "original_question": canonical_question,
                "normalized_question": canonical_question,
                "metrics": merged_metrics,
                "dimensions": merged_dimensions,
                "semantic_metrics": merged_semantic_metrics,
                "semantic_dimensions": merged_semantic_dimensions,
                "time_range": merged_time,
                "confidence": max(answer_intent.confidence, 0.8),
                "needs_clarification": False,
                "clarification": "",
                "source": "followup_resolver",
                "query_spec": query_spec,
            }
        )
        return FollowupResolution(decision="answer_pending", intent=intent)

    if (answer_intent.metrics or answer_intent.semantic_metrics) and "metrics" not in pending.missing_slots:
        return FollowupResolution(decision="new_question", intent=answer_intent)

    missing_slots = list(pending.missing_slots)
    if "metrics" in missing_slots and answer_intent.metrics:
        missing_slots.remove("metrics")
    if "time_range" in missing_slots and answer_intent.time_range:
        missing_slots.remove("time_range")
    return FollowupResolution(
        decision="still_pending",
        pending=pending.model_copy(
            update={
                "missing_slots": missing_slots,
                "clarification": pending.clarification,
            }
        ),
    )


def pending_from_intent(intent: ParsedQuestionIntent) -> PendingClarification:
    missing_slots: list[Literal["metrics", "time_range"]] = []
    if not intent.metrics:
        missing_slots.append("metrics")
    if _requires_time_clarification(intent.original_question) and not intent.time_range:
        missing_slots.append("time_range")
    return PendingClarification(
        original_question=intent.original_question,
        parsed_intent=intent.model_dump(mode="json"),
        query_spec=intent.query_spec,
        missing_slots=missing_slots or ["metrics"],
        clarification=intent.clarification,
        created_at=datetime.now(timezone.utc),
    )


def _render_canonical_question(original_question: str, metrics: list[str], dimensions: list[str], time_range: str) -> str:
    # This is a rendering of verified slots, not a concatenation of untrusted conversation text.
    parts = [original_question.strip()]
    if metrics:
        parts.append("指标为" + "、".join(METRIC_LABELS[item] for item in metrics if item in METRIC_LABELS))
    if dimensions:
        parts.append("维度为" + "、".join(DIMENSION_LABELS[item] for item in dimensions if item in DIMENSION_LABELS))
    if time_range:
        parts.append("时间范围为" + time_range)
    return "；".join(part for part in parts if part)


def _merge(existing: list[str], incoming: list[str]) -> list[str]:
    return list(dict.fromkeys([*existing, *incoming]))


def _requires_time_clarification(question: str) -> bool:
    return any(token in question for token in ("哪段时间", "什么时间", "时间范围", "从什么时候", "何时"))
