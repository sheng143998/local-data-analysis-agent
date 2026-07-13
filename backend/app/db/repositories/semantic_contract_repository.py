import json
from uuid import UUID, uuid4

from backend.app.db.connection import get_connection
from backend.app.schemas.semantic_contracts import (
    SemanticContract,
    SemanticContractCreate,
    SemanticContractStatus,
    SemanticContractType,
)


class SemanticContractRepository:
    """Semantic Layer V2 的版本化业务契约仓储。"""

    def get_active(self, contract_key: str) -> SemanticContract | None:
        """读取最新启用版本，历史记录仅用于追溯，不能被默认解析路径误用。"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                _SELECT_CONTRACT
                + """
                WHERE contract_key = %s AND status = 'enabled'
                ORDER BY version DESC
                LIMIT 1
                """,
                (contract_key,),
            )
            row = cursor.fetchone()
            return _row_to_contract(row) if row else None

    def list_enabled(
        self, contract_type: SemanticContractType | None = None
    ) -> list[SemanticContract]:
        with get_connection() as conn:
            cursor = conn.cursor()
            if contract_type is None:
                cursor.execute(
                    _SELECT_CONTRACT
                    + """
                    WHERE status = 'enabled'
                    ORDER BY contract_type, contract_key, version DESC
                    """
                )
            else:
                cursor.execute(
                    _SELECT_CONTRACT
                    + """
                    WHERE status = 'enabled' AND contract_type = %s
                    ORDER BY contract_key, version DESC
                    """,
                    (contract_type,),
                )
            return [_row_to_contract(row) for row in cursor.fetchall()]

    def create(self, payload: SemanticContractCreate) -> SemanticContract:
        """只新增版本，不提供更新方法，防止业务口径在原版本上被静默改写。"""
        contract_id = uuid4()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO semantic_contracts (
                  id, contract_key, version, contract_type, display_name,
                  business_definition, source_tables, source_fields, synonyms,
                  default_filters, time_grain, aggregation, semantic_config,
                  owner, status
                )
                VALUES (
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
                  %s, %s, %s::jsonb, %s, %s
                )
                """,
                (
                    str(contract_id),
                    payload.contract_key,
                    payload.version,
                    payload.contract_type,
                    payload.display_name,
                    payload.business_definition,
                    payload.source_tables,
                    payload.source_fields,
                    payload.synonyms,
                    json.dumps(payload.default_filters, ensure_ascii=False),
                    payload.time_grain,
                    payload.aggregation,
                    json.dumps(payload.semantic_config, ensure_ascii=False),
                    payload.owner,
                    payload.status,
                ),
            )
            cursor.execute(_SELECT_CONTRACT + " WHERE id = %s", (str(contract_id),))
            row = cursor.fetchone()
        if row is None:
            raise RuntimeError("语义契约创建后无法读取")
        return _row_to_contract(row)


_SELECT_CONTRACT = """
SELECT id, contract_key, version, contract_type, display_name,
       business_definition, source_tables, source_fields, synonyms,
       default_filters, time_grain, aggregation, semantic_config,
       owner, status, created_at
FROM semantic_contracts
"""


def _row_to_contract(row) -> SemanticContract:
    default_filters = _load_json(row[9])
    semantic_config = _load_json(row[12])
    return SemanticContract(
        id=row[0],
        contract_key=row[1],
        version=row[2],
        contract_type=row[3],
        display_name=row[4],
        business_definition=row[5],
        source_tables=list(row[6] or []),
        source_fields=list(row[7] or []),
        synonyms=list(row[8] or []),
        default_filters=default_filters,
        time_grain=row[10],
        aggregation=row[11],
        semantic_config=semantic_config,
        owner=row[13],
        status=row[14],
        created_at=row[15],
    )


def _load_json(value: object) -> dict:
    if isinstance(value, str):
        return json.loads(value)
    return value or {}
