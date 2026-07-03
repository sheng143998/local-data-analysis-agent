from typing import Literal

from pydantic import BaseModel, Field


PathType = Literal["fast_path", "rewrite_path", "cold_path"]


class AnalyzeRequest(BaseModel):
    question: str = Field(default="", description="用户输入的自然语言业务问题")


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
