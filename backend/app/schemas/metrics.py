from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


MetricStatus = Literal["enabled", "draft", "disabled"]


class MetricBase(BaseModel):
    metric_name: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    formula: str = Field(min_length=1)
    required_tables: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    default_filters: dict[str, str] = Field(default_factory=dict)
    example_question: str = ""
    owner: str = "经营分析组"
    status: MetricStatus = "enabled"


class MetricCreate(MetricBase):
    pass


class MetricUpdate(BaseModel):
    metric_name: str | None = None
    display_name: str | None = None
    description: str | None = None
    formula: str | None = None
    required_tables: list[str] | None = None
    required_fields: list[str] | None = None
    default_filters: dict[str, str] | None = None
    example_question: str | None = None
    owner: str | None = None
    status: MetricStatus | None = None


class MetricDefinition(MetricBase):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
