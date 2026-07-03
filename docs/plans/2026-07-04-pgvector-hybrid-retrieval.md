# pgvector 混合检索接入计划

## Goal

把上一模块写入的 `schema_metadata.embedding` 和 `metric_definitions.embedding` 接入 schema/metric retriever，让字段和指标召回从纯文本规则走向文本分数 + 向量语义分数的混合检索。普通用户界面仍不展示 embedding provider、向量状态、模型状态或调试细节。

## Current task

当前正在做：实现 pgvector 语义候选查询 helper，并接入 metric/schema retriever 的评分。

## Scope

包含：

- 新增可复用的 pgvector 检索工具。
- 对用户问题调用 `EmbeddingAdapter` 生成查询向量。
- 从 `metric_definitions.embedding` 查询 metric 语义候选。
- 从 `schema_metadata.embedding` 查询 schema 语义候选。
- 将 semantic score 纳入已有文本/关键词/结构化评分。
- embedding 或数据库向量不可用时退回现有检索，不影响 `/api/analyze` 可用性。
- 增加 focused unit tests。
- 更新 README、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端展示。
- 不接入 SQL Memory question/sql embedding。
- 不要求真实外部 embedding provider 才能运行测试。

## Module boundary

上游输入：

- 用户问题文本。
- `EmbeddingAdapter` 生成的查询向量。
- 已同步的 `schema_metadata.embedding`、`metric_definitions.embedding`。

下游输出：

- retriever 内部的 `semantic_score` 和混合 `score`。
- `MetricContext` 和 `SchemaColumnContext` 的最终排序结果。

预计触达文件：

- `backend/app/tools/vector_retrieval.py`
- `backend/app/tools/metric_retriever.py`
- `backend/app/tools/schema_retriever.py`
- `backend/app/schemas/retrieval.py`
- `backend/tests/test_vector_retrieval.py`
- `backend/tests/test_retrieval_scoring.py` 或 `backend/tests/test_retrieval_tools.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-pgvector-hybrid-retrieval.md`

## Business logic

换库或换表后，系统不应该靠继续堆固定模板理解问题。字段说明和指标口径已经可以写入向量，本模块让检索链路开始使用这些向量：当用户问“退款表现”“商品利润”这类不完全命中关键词的问题时，系统可以通过语义候选补强召回；当向量不可用时，仍保持原来的稳定文本检索。

## Data contract

- `MetricContext.semantic_score`: 内部语义召回分，默认 `0`。
- `SchemaColumnContext.semantic_score`: 内部语义召回分，默认 `0`。
- `VectorCandidate.score`: `1 - cosine_distance` 的归一化分数，范围裁剪到 `0..1`。

## Implementation steps

- [x] 读取 handoff、retriever、scoring、schema 和现有测试。
- [x] 实现 pgvector 查询 helper。
- [x] 接入 metric/schema retriever。
- [x] 增加单元测试。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `npm run backend:test`，101 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

本模块改变后端检索排序基础层，但不改变前端和 API 字段主契约；已补跑标准评估观察基线。

## Risks and open questions

- deterministic embedding 只是本地 fallback，真实语义质量依赖真实 embedding provider。
- 如果用户尚未运行 `sync_embeddings.py`，语义候选为空，系统会退回现有检索。
- `semantic_score` 暂作为内部评分字段，普通用户 UI 不展示。
