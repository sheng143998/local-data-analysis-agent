import pytest

from backend.app.services.context_refresh_service import ContextRefreshService, _normalize_targets
from backend.app.services.embedding_sync_service import EmbeddingSyncResult
from backend.app.services.schema_sync_service import SchemaSyncResult


class FakeSchemaService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def sync_public_schema(self, include_tables=None, exclude_tables=None) -> SchemaSyncResult:
        self.calls.append(
            {
                "include_tables": include_tables,
                "exclude_tables": exclude_tables,
            }
        )
        return SchemaSyncResult(
            scanned_columns=3,
            synced_columns=3,
            tables=["orders", "users"],
        )


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int | None]] = []

    def sync_all(
        self,
        limit=None,
        batch_size=16,
        retry_single_on_batch_failure=True,
        sleep_ms=0,
    ) -> list[EmbeddingSyncResult]:
        self.calls.append(("all", limit, batch_size, retry_single_on_batch_failure, sleep_ms))
        return [
            EmbeddingSyncResult(target="schema", scanned=3, updated=3),
            EmbeddingSyncResult(target="metric", scanned=1, updated=1),
            EmbeddingSyncResult(target="memory", scanned=2, updated=2),
        ]

    def sync_schema_embeddings(
        self,
        limit=None,
        batch_size=16,
        retry_single_on_batch_failure=True,
        sleep_ms=0,
    ) -> EmbeddingSyncResult:
        self.calls.append(("schema", limit, batch_size, retry_single_on_batch_failure, sleep_ms))
        return EmbeddingSyncResult(target="schema", scanned=3, updated=3)

    def sync_metric_embeddings(
        self,
        limit=None,
        batch_size=16,
        retry_single_on_batch_failure=True,
        sleep_ms=0,
    ) -> EmbeddingSyncResult:
        self.calls.append(("metric", limit, batch_size, retry_single_on_batch_failure, sleep_ms))
        return EmbeddingSyncResult(target="metric", scanned=1, updated=1)

    def sync_sql_memory_embeddings(
        self,
        limit=None,
        batch_size=16,
        retry_single_on_batch_failure=True,
        sleep_ms=0,
    ) -> EmbeddingSyncResult:
        self.calls.append(("memory", limit, batch_size, retry_single_on_batch_failure, sleep_ms))
        return EmbeddingSyncResult(target="memory", scanned=2, updated=2)


def test_refresh_syncs_schema_then_all_embeddings_by_default() -> None:
    schema_service = FakeSchemaService()
    embedding_service = FakeEmbeddingService()
    service = ContextRefreshService(
        schema_service=schema_service,
        embedding_service=embedding_service,
    )

    result = service.refresh()

    assert schema_service.calls == [{"include_tables": None, "exclude_tables": None}]
    assert embedding_service.calls == [("all", None, 16, True, 0)]
    assert result.schema_result.synced_columns == 3
    assert [item.target for item in result.embedding_results] == ["schema", "metric", "memory"]


def test_refresh_passes_table_filters_and_can_skip_embeddings() -> None:
    schema_service = FakeSchemaService()
    embedding_service = FakeEmbeddingService()
    service = ContextRefreshService(
        schema_service=schema_service,
        embedding_service=embedding_service,
    )

    result = service.refresh(
        include_tables=["orders"],
        exclude_tables=["tmp_import"],
        sync_embeddings=False,
    )

    assert schema_service.calls == [
        {
            "include_tables": ["orders"],
            "exclude_tables": ["tmp_import"],
        }
    ]
    assert embedding_service.calls == []
    assert result.embedding_results == []


def test_refresh_syncs_selected_embedding_targets_in_order() -> None:
    embedding_service = FakeEmbeddingService()
    service = ContextRefreshService(
        schema_service=FakeSchemaService(),
        embedding_service=embedding_service,
    )

    result = service.refresh(
        embedding_targets=["memory", "schema", "memory"],
        embedding_limit=10,
        embedding_batch_size=4,
        retry_single_on_batch_failure=False,
        embedding_sleep_ms=200,
    )

    assert embedding_service.calls == [("memory", 10, 4, False, 200), ("schema", 10, 4, False, 200)]
    assert [item.target for item in result.embedding_results] == ["memory", "schema"]


def test_normalize_targets_rejects_unknown_target() -> None:
    with pytest.raises(ValueError, match="unsupported embedding target"):
        _normalize_targets(["schema", "bad"])  # type: ignore[list-item]
