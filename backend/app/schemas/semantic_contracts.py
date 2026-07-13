from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


SemanticContractType = Literal["metric", "dimension", "entity", "relationship"]
SemanticContractStatus = Literal["enabled", "draft", "disabled"]


class SemanticContractBase(BaseModel):
    """语义层可审计的业务定义，不包含可直接执行的 SQL。"""

    contract_key: str = Field(min_length=1, max_length=120)
    contract_type: SemanticContractType
    display_name: str = Field(min_length=1, max_length=200)
    business_definition: str = Field(min_length=1)
    source_tables: list[str] = Field(default_factory=list)
    source_fields: list[str] = Field(default_factory=list)
    synonyms: list[str] = Field(default_factory=list)
    default_filters: dict[str, Any] = Field(default_factory=dict)
    time_grain: str = ""
    aggregation: str = ""
    semantic_config: dict[str, Any] = Field(default_factory=dict)
    owner: str = ""
    status: SemanticContractStatus = "draft"


class SemanticContractCreate(SemanticContractBase):
    """创建新版本时由调用方显式声明版本，避免静默覆盖既有口径。"""

    version: int = Field(ge=1)


class SemanticContract(SemanticContractCreate):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
