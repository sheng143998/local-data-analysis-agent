# EmbeddingAdapter 基础层计划

## Goal

本模块新增统一 EmbeddingAdapter 基础层，为 schema、metric、SQL Memory 后续接入 pgvector 混合检索提供稳定入口。它不新增固定 SQL 模板，不写入数据库向量，也不在普通用户界面展示模型或向量状态。

## Current task

当前正在做：验证已通过，准备提交并推送。

## Scope

包含：

- 新增 embedding 相关配置项。
- 新增 `backend/app/core/embedding_adapter.py`。
- 支持 OpenAI-compatible `/embeddings` 请求。
- 支持 deterministic provider，用于本地开发和测试无外部服务生成稳定向量。
- 结构化响应、错误、latency、usage。
- 单元测试覆盖 payload、Authorization、空输入、HTTP 错误、transport 错误、deterministic fallback。
- 更新 `.env.example`、README、handoff 和模块完成说明。

不包含：

- 不调用真实外部 embedding 服务。
- 不生成或写入 `schema_metadata.embedding`、`metric_definitions.embedding`、`sql_memories.question_embedding`。
- 不修改数据库 migration。
- 不把 embedding 状态展示给普通用户。
- 不新增 SQL 模板。

## Module boundary

上游输入：

- schema 文档文本。
- metric 文档文本。
- SQL Memory question/sql 文本。

下游输出：

- `EmbeddingResponse`，包含 `vectors`、provider、model、dimension、latency、usage 和结构化错误。

预计触达文件：

- `backend/app/core/config.py`
- `backend/app/core/embedding_adapter.py`
- `backend/.env.example`
- `backend/tests/test_embedding_adapter.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-embedding-adapter-foundation.md`

## Business logic

后续换库或新增表字段后，系统需要把 schema、指标和历史 SQL 变成可检索的向量。本模块先把“如何生成 embedding”收口到统一 adapter，避免后续各个检索节点直接调用不同 SDK 或服务。

## Data contract

新增类型：

- `EmbeddingRequest`
  - `texts: list[str]`
  - `trace_id: str | None`
- `EmbeddingResponse`
  - `ok: bool`
  - `vectors: list[list[float]]`
  - `provider: str`
  - `model: str`
  - `dimension: int`
  - `latency_ms: int`
  - `usage: EmbeddingUsage`
  - `error_code: str | None`
  - `error_message: str | None`

配置：

- `EMBEDDING_PROVIDER`
- `EMBEDDING_BASE_URL`
- `EMBEDDING_MODEL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_DIMENSIONS`
- `EMBEDDING_TIMEOUT_SECONDS`
- `EMBEDDING_MAX_RETRIES`

## Implementation steps

- [x] 读取 handoff、ModelAdapter 和现有配置。
- [x] 实现 EmbeddingAdapter 基础层。
- [x] 增加单元测试和 `.env.example`。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`

本模块不修改 `/api/analyze` 执行语义，暂不强制运行 `npm run eval:standard`。

## Risks and open questions

- deterministic provider 只用于本地 fallback 和测试，不代表真实语义 embedding。
- 后续接入数据库向量写入时，需要新增脚本和批量更新策略。
- 后续如果 OpenAI-compatible provider 的响应字段差异较大，需要扩展解析逻辑。
