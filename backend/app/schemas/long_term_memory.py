from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


MemoryStatus = Literal["active", "superseded", "revoked"]


class LongTermMemory(BaseModel):
    id: UUID
    memory_key: str
    category: str
    value: dict[str, str] = Field(default_factory=dict)
    status: MemoryStatus
    version: int
    created_at: datetime
    updated_at: datetime


class RememberedPreference(BaseModel):
    memory_key: str
    category: str
    value: dict[str, str]
