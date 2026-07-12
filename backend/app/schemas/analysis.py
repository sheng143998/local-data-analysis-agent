from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


PathType = Literal["fast_path", "rewrite_path", "cold_path"]


class AnalyzeRequest(BaseModel):
    question: str = Field(default="", description="用户输入的自然语言业务问题")
    conversation_id: UUID | None = Field(default=None, description="可选的会话标识；缺省时创建新会话")


class AnalysisMetric(BaseModel):
    label: str
    value: str
    delta: str
    hint: str


AnalysisValue = str | int | float | bool | None
AnalysisRow = dict[str, AnalysisValue]


class AnalysisSource(BaseModel):
    dataset: str
    tables: list[str]
    fields: list[str]
    metricDefinition: str
    range: str
    returnedRows: int
    queryTime: str
    security: str


class AnalysisTrace(BaseModel):
    toolCalls: int
    modelCalls: int
    memoryCandidates: int
    totalTime: str


class AgentStep(BaseModel):
    name: str
    status: Literal["已完成", "运行中", "已跳过"]
    time: str


class AnalyzeResponse(BaseModel):
    question: str
    path: PathType
    summary: str
    sql: str
    metrics: list[AnalysisMetric]
    rows: list[AnalysisRow]
    source: AnalysisSource
    trace: AnalysisTrace
    steps: list[AgentStep]
    conversation_id: UUID | None = None
    pending_clarification: bool = False
    conversation_status: Literal["active", "waiting_for_clarification", "cancelled"] = "active"


class ConversationMessage(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    response: dict[str, Any] | None = None


class ConversationSummary(BaseModel):
    id: UUID
    title: str
    updated_at: datetime
    status: Literal["active", "waiting_for_clarification", "cancelled"]


class ConversationDetail(ConversationSummary):
    messages: list[ConversationMessage] = Field(default_factory=list)
