# Embedding 批量失败单条重试计划

## Goal

Embedding 同步已经支持 batch 请求，但当前 batch 返回错误或向量数量不足时，会把整批记录都标记失败。真实 provider 下可能只有单条文本触发问题，本模块增加 batch 失败后的单条重试，避免一条坏记录拖垮整批。

## Current task

当前正在做：Embedding 批量失败单条重试已完成实现、文档和验证，等待 commit 并 push。

## Scope

包含：

- schema embedding batch 失败后单条重试。
- metric embedding batch 失败后单条重试。
- SQL Memory embedding batch 失败后按单条 memory 的问题/SQL 成对重试。
- `sync_all()` 和 `ContextRefreshService` 透传 `retry_single_on_batch_failure`。
- focused tests、README、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端。
- 不改变 `/api/analyze` 主链路。
- 不实现并发、限速或后台任务。

## Module boundary

上游输入：

- `EmbeddingAdapter.embed()` 的 batch 响应。
- schema、metric、memory 同步记录。

下游输出：

- 成功的单条记录继续写回 embedding。
- 真正失败的记录才进入 `EmbeddingSyncResult.failed/errors`。

预计触达文件：

- `backend/app/services/embedding_sync_service.py`
- `backend/app/services/context_refresh_service.py`
- `backend/tests/test_embedding_sync_service.py`
- `backend/tests/test_context_refresh_service.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-embedding-batch-single-retry.md`

## Business logic

开发者同步大量向量时，batch 可以减少请求次数；当某个 batch 失败时，系统自动降级为单条请求，最大化保留可同步记录，并把真正失败的记录写入错误摘要，便于后续处理。

## Data contract

不新增 API 字段。内部服务新增可选参数：

- `retry_single_on_batch_failure: bool = True`

## Implementation steps

- [x] 读取 handoff、同步服务和测试。
- [x] 实现 batch 失败单条重试。
- [x] 增加 focused tests。
- [x] 更新 README、handoff 和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，28 passed
- `npm run backend:test`，129 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- 单条重试会增加失败 batch 的请求次数，但只在 batch 失败时触发。
- 仍未实现 provider 级限速和后台队列。
