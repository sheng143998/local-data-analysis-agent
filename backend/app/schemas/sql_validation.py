from pydantic import BaseModel, Field


DEFAULT_ALLOWED_TABLES = [
    "users",
    "products",
    "orders",
    "order_items",
    "payments",
    "refunds",
    "reviews",
    "traffic_events",
    "coupons",
    "coupon_usages",
    "inventory_snapshots",
    "product_costs",
]


class SqlValidationRequest(BaseModel):
    sql: str = Field(min_length=1)
    allowed_tables: list[str] = Field(default_factory=lambda: DEFAULT_ALLOWED_TABLES.copy())
    max_rows: int = 1000


class SqlValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    tables: list[str] = Field(default_factory=list)
    normalized_sql: str = ""


class SqlGuardResult(BaseModel):
    allowed: bool
    final_sql: str = ""
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
