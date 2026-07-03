from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from backend.app.services.embedding_sync_service import EmbeddingSyncResult, EmbeddingSyncService
from backend.app.services.schema_sync_service import SchemaSyncResult, SchemaSyncService


RefreshEmbeddingTarget = Literal["schema", "metric", "memory"]


@dataclass(frozen=True)
class ContextRefreshResult:
    schema_result: SchemaSyncResult
    embedding_results: list[EmbeddingSyncResult]


class ContextRefreshService:
    """刷新换库/换表后的检索上下文资产。"""

    def __init__(
        self,
        schema_service: SchemaSyncService | None = None,
        embedding_service: EmbeddingSyncService | None = None,
    ) -> None:
        self.schema_service = schema_service or SchemaSyncService()
        self.embedding_service = embedding_service or EmbeddingSyncService()

    def refresh(
        self,
        *,
        include_tables: Iterable[str] | None = None,
        exclude_tables: Iterable[str] | None = None,
        sync_embeddings: bool = True,
        embedding_targets: Iterable[RefreshEmbeddingTarget] | None = None,
        embedding_limit: int | None = None,
        embedding_batch_size: int = 16,
        retry_single_on_batch_failure: bool = True,
    ) -> ContextRefreshResult:
        schema_result = self.schema_service.sync_public_schema(
            include_tables=include_tables,
            exclude_tables=exclude_tables,
        )
        embedding_results = (
            self._sync_embeddings(
                embedding_targets,
                limit=embedding_limit,
                batch_size=embedding_batch_size,
                retry_single_on_batch_failure=retry_single_on_batch_failure,
            )
            if sync_embeddings
            else []
        )
        return ContextRefreshResult(
            schema_result=schema_result,
            embedding_results=embedding_results,
        )

    def _sync_embeddings(
        self,
        embedding_targets: Iterable[RefreshEmbeddingTarget] | None,
        *,
        limit: int | None = None,
        batch_size: int = 16,
        retry_single_on_batch_failure: bool = True,
    ) -> list[EmbeddingSyncResult]:
        targets = _normalize_targets(embedding_targets)
        if targets == ["schema", "metric", "memory"]:
            return self.embedding_service.sync_all(
                limit=limit,
                batch_size=batch_size,
                retry_single_on_batch_failure=retry_single_on_batch_failure,
            )

        results: list[EmbeddingSyncResult] = []
        for target in targets:
            if target == "schema":
                results.append(
                    self.embedding_service.sync_schema_embeddings(
                        limit=limit,
                        batch_size=batch_size,
                        retry_single_on_batch_failure=retry_single_on_batch_failure,
                    )
                )
            elif target == "metric":
                results.append(
                    self.embedding_service.sync_metric_embeddings(
                        limit=limit,
                        batch_size=batch_size,
                        retry_single_on_batch_failure=retry_single_on_batch_failure,
                    )
                )
            elif target == "memory":
                results.append(
                    self.embedding_service.sync_sql_memory_embeddings(
                        limit=limit,
                        batch_size=batch_size,
                        retry_single_on_batch_failure=retry_single_on_batch_failure,
                    )
                )
        return results


def _normalize_targets(
    embedding_targets: Iterable[RefreshEmbeddingTarget] | None,
) -> list[RefreshEmbeddingTarget]:
    if not embedding_targets:
        return ["schema", "metric", "memory"]

    ordered: list[RefreshEmbeddingTarget] = []
    for target in embedding_targets:
        if target not in {"schema", "metric", "memory"}:
            raise ValueError(f"unsupported embedding target: {target}")
        if target not in ordered:
            ordered.append(target)
    return ordered or ["schema", "metric", "memory"]
