from pydantic import BaseModel, Field


class QueryMeasure(BaseModel):
    name: str
    operation: str = ""


class QueryPlan(BaseModel):
    entities: list[str] = Field(default_factory=list)
    measures: list[QueryMeasure] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    filters: list[str] = Field(default_factory=list)
    time_filter: str = ""
    order_by: list[str] = Field(default_factory=list)
    limit: int | None = None
    expected_columns: list[str] = Field(default_factory=list)
    expected_row_shape: str = "unknown"
    contract_keys: list[str] = Field(default_factory=list)
