from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.schemas.analysis import ConversationDetail, ConversationMessage, ConversationSummary
from backend.app.schemas.query_spec import QuerySpec


class PendingClarification(BaseModel):
    original_question: str
    parsed_intent: dict = Field(default_factory=dict)
    query_spec: QuerySpec = Field(default_factory=QuerySpec)
    missing_slots: list[Literal["metrics", "time_range"]] = Field(default_factory=list)
    clarification: str
    created_at: datetime


class CurrentAnalysis(BaseModel):
    original_question: str
    query_spec: QuerySpec = Field(default_factory=QuerySpec)
    stage: Literal["waiting_for_clarification", "executing", "completed", "cancelled"]
    updated_at: datetime


class ConversationState(BaseModel):
    id: UUID
    owner_id: UUID | None = None
    title: str
    created_at: datetime
    updated_at: datetime
    status: Literal["active", "waiting_for_clarification", "cancelled"] = "active"
    messages: list[ConversationMessage] = Field(default_factory=list)
    pending_clarification: PendingClarification | None = None
    current_analysis: CurrentAnalysis | None = None
    rolling_summary: str = ""
    summary_version: int = 0
    summary_token_estimate: int = 0

    def summary(self) -> ConversationSummary:
        return ConversationSummary(id=self.id, title=self.title, updated_at=self.updated_at, status=self.status)

    def detail(self, *, limit: int, before: UUID | None = None) -> ConversationDetail:
        """按时间正序返回消息窗口，供前端向上加载更早会话内容。"""
        end = len(self.messages)
        if before is not None:
            for index, message in enumerate(self.messages):
                if message.id == before:
                    end = index
                    break
            else:
                raise ValueError("消息分页游标不属于当前会话")
        start = max(0, end - limit)
        has_more = start > 0
        return ConversationDetail(
            **self.summary().model_dump(),
            messages=self.messages[start:end],
            has_more=has_more,
            next_before=self.messages[start].id if has_more else None,
        )
