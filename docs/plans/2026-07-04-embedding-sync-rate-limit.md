# Embedding 同步批次限速计划

## Goal

当前 embedding 同步已经支持 limit、batch 和 batch 失败单条重试，但真实 embedding provider 往往有 QPS 或 RPM 限制。本模块增加批次间 `sleep_ms`，让开发者可以在大规模同步时主动降低请求频率。

## Current task

当前正在做：Embedding 同步批次限速已完成实现、文档和验证，等待 commit 并 push。

## Scope

包含：

- `EmbeddingSyncService` 支持 `sleep_ms`。
- schema、metric、SQL Memory batch 之间按需等待。
- batch 失败后的单条重试之间也按需等待，避免重试时打满 provider。
- `ContextRefreshService` 透传 `embedding_sleep_ms`。
- `sync_embeddings.py` 增加 `--sleep-ms`。
- `refresh_context.py` 增加 `--embedding-sleep-ms`。
- focused tests、README、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端。
- 不改变 `/api/analyze` 主链路。
- 不实现后台队列或自动速率探测。

## Module boundary

上游输入：

- CLI 参数 `--sleep-ms` / `--embedding-sleep-ms`。
- 当前同步目标记录和 batch 设置。

下游输出：

- embedding 写回行为不变。
- 同步过程在连续请求之间按需等待。

预计触达文件：

- `backend/app/services/embedding_sync_service.py`
- `backend/app/services/context_refresh_service.py`
- `backend/scripts/sync_embeddings.py`
- `backend/scripts/refresh_context.py`
- `backend/tests/test_embedding_sync_service.py`
- `backend/tests/test_context_refresh_service.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-embedding-sync-rate-limit.md`

## Business logic

开发者可以用 `--sleep-ms 200` 这类参数让 embedding 同步在批次之间暂停，避免真实 provider 因请求过密返回限流错误。默认 `0` 保持当前速度。

## Data contract

不新增 API 字段。内部服务新增可选参数：

- `sleep_ms: int = 0`

CLI 新增：

- `py -3 backend/scripts/sync_embeddings.py --sleep-ms 200`
- `py -3 backend/scripts/refresh_context.py --embedding-sleep-ms 200`

## Implementation steps

- [x] 读取 handoff 和当前同步服务。
- [x] 实现服务和 CLI 限速参数。
- [x] 增加 focused tests。
- [x] 更新 README、handoff 和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，32 passed
- `py -3 backend/scripts/sync_embeddings.py --help`，通过
- `py -3 backend/scripts/refresh_context.py --help`，通过
- `npm run backend:test`，133 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- `sleep_ms` 是固定等待，不是自适应限速。
- 后续仍可增加后台任务、断点游标和 provider 错误码驱动的指数退避。
