from pydantic import BaseModel, Field


class QueryMeasure(BaseModel):
    name: str
    operation: str = ""


class QueryContractConstraint(BaseModel):
    """已审核业务合同在 SQL 生成和校验阶段的最小可执行约束。"""

    contract_key: str
    display_name: str = ""
    aggregation: str = ""
    source_tables: list[str] = Field(default_factory=list)
    source_fields: list[str] = Field(default_factory=list)


class QueryExecutionContract(BaseModel):
    """SQL 生成必须遵守的本次业务执行约束，不包含固定 SQL。"""

    time_field: str = ""
    time_predicate: str = ""
    time_group_expression: str = ""
    canonical_filters: list[str] = Field(default_factory=list)
    join_strategy: list[str] = Field(default_factory=list)
    aggregation_grain: str = ""
    output_aliases: dict[str, str] = Field(default_factory=dict)


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
    contract_constraints: list[QueryContractConstraint] = Field(default_factory=list)
    execution_contract: QueryExecutionContract = Field(default_factory=QueryExecutionContract)
