from pydantic import BaseModel, Field


class QuerySpec(BaseModel):
    """Structured business requirements shared by generation, validation, and memory."""

    metrics: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    time_range: str = ""
    time_start: str = ""
    time_end: str = ""
    time_filter: str = ""
    granularity: str | None = None
    top_n: int | None = None
    requires_order_by: bool = False
    required_table_groups: list[list[str]] = Field(default_factory=list)
    required_metric_tokens: list[str] = Field(default_factory=list)
    required_dimension_tokens: list[str] = Field(default_factory=list)
    required_output_tokens: list[str] = Field(default_factory=list)
    forbidden_sql_patterns: list[str] = Field(default_factory=list)

    @property
    def required_tables(self) -> list[str]:
        return sorted({table for group in self.required_table_groups for table in group})
