from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from backend.app.db.repositories import semantic_contract_repository
from backend.app.db.repositories.semantic_contract_repository import SemanticContractRepository
from backend.app.schemas.semantic_contracts import SemanticContractCreate


def _contract_row(contract_id=None, *, version: int = 1, status: str = "enabled"):
    return (
        contract_id or uuid4(),
        "sales_amount",
        version,
        "metric",
        "销售额",
        "已支付订单的去重订单金额之和",
        ["orders", "payments"],
        ["orders.total_amount", "payments.status"],
        ["成交额", "GMV"],
        '{"payment_status":"paid"}',
        "day",
        "sum",
        '{"requires_distinct_order":true}',
        "经营分析组",
        status,
        datetime.now(timezone.utc),
    )


class _FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executions = []

    def execute(self, query, parameters=()):
        self.executions.append((query, parameters))

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class _FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


def _fake_connection(cursor):
    @contextmanager
    def factory():
        yield _FakeConnection(cursor)

    return factory


def test_semantic_contract_schema_rejects_invalid_version() -> None:
    try:
        SemanticContractCreate(
            contract_key="sales_amount",
            version=0,
            contract_type="metric",
            display_name="销售额",
            business_definition="已支付订单金额",
        )
    except ValueError as error:
        assert "version" in str(error)
    else:
        raise AssertionError("版本号为零时必须拒绝创建语义契约")


def test_get_active_reads_latest_enabled_version_with_bound_parameter(monkeypatch) -> None:
    cursor = _FakeCursor([_contract_row(version=3)])
    monkeypatch.setattr(
        semantic_contract_repository, "get_connection", _fake_connection(cursor)
    )

    contract = SemanticContractRepository().get_active("sales_amount")

    assert contract is not None
    assert contract.version == 3
    assert contract.default_filters == {"payment_status": "paid"}
    assert "status = 'enabled'" in cursor.executions[0][0]
    assert cursor.executions[0][1] == ("sales_amount",)


def test_create_inserts_new_version_and_returns_persisted_contract(monkeypatch) -> None:
    contract_id = uuid4()
    cursor = _FakeCursor([_contract_row(contract_id, version=2, status="draft")])
    monkeypatch.setattr(
        semantic_contract_repository, "get_connection", _fake_connection(cursor)
    )
    monkeypatch.setattr(semantic_contract_repository, "uuid4", lambda: contract_id)
    payload = SemanticContractCreate(
        contract_key="sales_amount",
        version=2,
        contract_type="metric",
        display_name="销售额",
        business_definition="已支付订单的去重订单金额之和",
        source_tables=["orders", "payments"],
        default_filters={"payment_status": "paid"},
        semantic_config={"requires_distinct_order": True},
    )

    contract = SemanticContractRepository().create(payload)

    insert_query, insert_parameters = cursor.executions[0]
    assert "INSERT INTO semantic_contracts" in insert_query
    assert insert_parameters[0] == str(contract_id)
    assert insert_parameters[2] == 2
    assert insert_parameters[9] == '{"payment_status": "paid"}'
    assert contract.id == contract_id
    assert contract.status == "draft"


def test_list_enabled_can_filter_by_contract_type(monkeypatch) -> None:
    cursor = _FakeCursor([_contract_row()])
    monkeypatch.setattr(
        semantic_contract_repository, "get_connection", _fake_connection(cursor)
    )

    contracts = SemanticContractRepository().list_enabled("metric")

    assert [contract.contract_key for contract in contracts] == ["sales_amount"]
    assert cursor.executions[0][1] == ("metric",)
