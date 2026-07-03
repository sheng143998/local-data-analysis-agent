from pydantic import BaseModel, Field


class MetricContext(BaseModel):
    metric_name: str
    display_name: str
    description: str
    formula: str
    required_tables: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    score: float


class SchemaColumnContext(BaseModel):
    table_name: str
    column_name: str
    data_type: str
    description: str
    business_meaning: str


class RetrievalContext(BaseModel):
    metrics: list[MetricContext] = Field(default_factory=list)
    schema_columns: list[SchemaColumnContext] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)
    metric_summary: str = ""
