from pydantic import BaseModel, Field


class MetricContext(BaseModel):
    metric_name: str
    display_name: str
    description: str
    formula: str
    required_tables: list[str] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    semantic_score: float = 0
    score: float


class SchemaColumnContext(BaseModel):
    table_name: str
    column_name: str
    data_type: str
    description: str
    business_meaning: str
    semantic_score: float = 0
    score: float = 0


class TableRelationshipContext(BaseModel):
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    relationship_type: str
    confidence: float
    reason: str


class RetrievalContext(BaseModel):
    metrics: list[MetricContext] = Field(default_factory=list)
    schema_columns: list[SchemaColumnContext] = Field(default_factory=list)
    table_relationships: list[TableRelationshipContext] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    fields: list[str] = Field(default_factory=list)
    metric_summary: str = ""
    rerank_diagnostics: dict = Field(default_factory=dict)
