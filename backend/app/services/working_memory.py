from dataclasses import dataclass
from math import ceil

from backend.app.core.config import settings
from backend.app.schemas.conversation import ConversationState


class TokenCounter:
    def count(self, text: str) -> int:
        raise NotImplementedError


class ConservativeCharacterTokenCounter(TokenCounter):
    """Tokenizer-free estimate that intentionally budgets Chinese text conservatively."""

    def count(self, text: str) -> int:
        return ceil(len(text) / 4) if text else 0


@dataclass(frozen=True)
class WorkingMemoryResult:
    context: str
    tokens_before: int
    tokens_after: int
    compression_level: str


def refresh_working_memory(state: ConversationState, counter: TokenCounter | None = None) -> WorkingMemoryResult:
    counter = counter or ConservativeCharacterTokenCounter()
    budget = settings.conversation_context_token_budget - settings.conversation_output_token_reserve
    raw_context = _render_context(state, message_limit=None)
    tokens_before = counter.count(raw_context)
    level = "none"
    if tokens_before > int(budget * settings.conversation_compression_aggressive_watermark):
        level = "aggressive"
        _update_summary(state, keep_recent=3, counter=counter)
    elif tokens_before > int(budget * settings.conversation_compression_light_watermark):
        level = "light"
        _update_summary(state, keep_recent=6, counter=counter)
    context = _render_context(state, message_limit=6 if level == "light" else 3 if level == "aggressive" else None)
    return WorkingMemoryResult(context=context, tokens_before=tokens_before, tokens_after=counter.count(context), compression_level=level)


def build_working_context(state: ConversationState, counter: TokenCounter | None = None) -> str:
    counter = counter or ConservativeCharacterTokenCounter()
    budget = settings.conversation_context_token_budget - settings.conversation_output_token_reserve
    context = _render_context(state, message_limit=None)
    if counter.count(context) <= budget:
        return context
    return _render_context(state, message_limit=3)


def _update_summary(state: ConversationState, *, keep_recent: int, counter: TokenCounter) -> None:
    older = state.messages[:-keep_recent] if len(state.messages) > keep_recent else []
    if not older:
        return
    facts = []
    if state.current_analysis:
        spec = state.current_analysis.query_spec
        facts.append(f"目标={state.current_analysis.original_question}")
        if spec.metrics:
            facts.append("指标=" + "、".join(spec.metrics))
        if spec.time_range:
            facts.append("时间=" + spec.time_range)
    if state.pending_clarification:
        facts.append("待补充=" + "、".join(state.pending_clarification.missing_slots))
    transcript = [f"{message.role}:{message.content[:240]}" for message in older[-20:]]
    state.rolling_summary = "\n".join([*facts, *transcript])[: settings.conversation_summary_char_limit]
    state.summary_version += 1
    state.summary_token_estimate = counter.count(state.rolling_summary)


def _render_context(state: ConversationState, message_limit: int | None) -> str:
    messages = state.messages if message_limit is None else state.messages[-message_limit:]
    blocks = []
    if state.rolling_summary:
        blocks.append("已压缩会话摘要：\n" + state.rolling_summary)
    if state.current_analysis:
        blocks.append("当前分析状态：" + state.current_analysis.model_dump_json(exclude_none=True))
    if state.pending_clarification:
        blocks.append("待澄清状态：" + state.pending_clarification.model_dump_json(exclude_none=True))
    if messages:
        blocks.append("最近对话：\n" + "\n".join(f"{message.role}: {message.content}" for message in messages))
    return "\n\n".join(blocks)
