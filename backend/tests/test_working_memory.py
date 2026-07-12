from datetime import datetime, timezone
from uuid import uuid4

from backend.app.core.config import settings
from backend.app.schemas.analysis import ConversationMessage
from backend.app.schemas.conversation import ConversationState, CurrentAnalysis, PendingClarification
from backend.app.schemas.query_spec import QuerySpec
from backend.app.services.working_memory import ConservativeCharacterTokenCounter, refresh_working_memory


def _state_with_messages(message_count: int, content: str) -> ConversationState:
    now = datetime.now(timezone.utc)
    state = ConversationState(id=uuid4(), title="test", created_at=now, updated_at=now)
    state.messages = [ConversationMessage(id=uuid4(), role="user" if index % 2 == 0 else "assistant", content=content, created_at=now) for index in range(message_count)]
    state.current_analysis = CurrentAnalysis(original_question="查询销售额", query_spec=QuerySpec(metrics=["sales_amount"], time_range="2017年"), stage="waiting_for_clarification", updated_at=now)
    state.pending_clarification = PendingClarification(original_question="查询销售额", query_spec=QuerySpec(metrics=["sales_amount"]), missing_slots=["time_range"], clarification="请补充时间", created_at=now)
    return state


def test_conservative_counter_handles_8000_token_boundaries() -> None:
    counter = ConservativeCharacterTokenCounter()
    assert counter.count("x" * (7999 * 4)) == 7999
    assert counter.count("x" * (8000 * 4)) == 8000
    assert counter.count("x" * (8001 * 4)) == 8001


def test_light_and_aggressive_compression_keep_pending_state(monkeypatch) -> None:
    monkeypatch.setattr(settings, "conversation_context_token_budget", 100)
    monkeypatch.setattr(settings, "conversation_output_token_reserve", 0)
    monkeypatch.setattr(settings, "conversation_compression_light_watermark", 0.6)
    monkeypatch.setattr(settings, "conversation_compression_aggressive_watermark", 0.8)
    monkeypatch.setattr(settings, "conversation_summary_char_limit", 1000)

    light = _state_with_messages(10, "轻量压缩内容" * 8)
    light_result = refresh_working_memory(light)
    assert light_result.compression_level in {"light", "aggressive"}
    assert light.rolling_summary
    assert "待补充=time_range" in light.rolling_summary
    assert light.pending_clarification is not None

    aggressive = _state_with_messages(20, "激进压缩内容" * 20)
    aggressive_result = refresh_working_memory(aggressive)
    assert aggressive_result.compression_level == "aggressive"
    assert aggressive.summary_version == 1
    assert aggressive.current_analysis is not None
