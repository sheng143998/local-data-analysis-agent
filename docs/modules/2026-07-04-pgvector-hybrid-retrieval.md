# 模块：pgvector 混合检索接入

当前状态：本模块已完成代码、测试和文档更新，并通过全量验证，随本次提交推送完成。它不新增固定 SQL 模板，不改变普通用户前端，也不展示 embedding provider、向量分数或数据库连接状态。

业务逻辑：schema 和 metric 的 embedding 写入后，检索链路需要真正使用这些向量。用户问题进入 `/api/analyze` 时，后端会为问题生成查询向量，通过 pgvector 召回 schema/metric 语义候选，并与已有关键词、文本相似度、必需表字段和业务规则分融合排序；如果 embedding 或 pgvector 不可用，则自动退回原有文本检索。

关键代码：

- `backend/app/tools/vector_retrieval.py`：统一生成问题向量、查询 `metric_definitions.embedding` / `schema_metadata.embedding`，把 cosine distance 转成 `semantic_score`，异常时返回空候选。
- `backend/app/tools/metric_retriever.py`：将 metric 语义候选分纳入指标总分。
- `backend/app/tools/schema_retriever.py`：将 schema 语义候选表并入加载范围，并将字段级语义分纳入排序。
- `backend/app/schemas/retrieval.py`：为 `MetricContext` 和 `SchemaColumnContext` 增加内部 `semantic_score` 字段。
- `backend/tests/test_vector_retrieval.py`、`backend/tests/test_retrieval_scoring.py`：覆盖 pgvector 查询形状、失败回退和语义分影响评分。

数据契约：

- `MetricContext.semantic_score`: 后端内部语义分，默认 `0`。
- `SchemaColumnContext.semantic_score`: 后端内部语义分，默认 `0`。
- `VectorCandidate.score`: `1 - cosine_distance` 后裁剪到 `0..1`。
- 普通 `AnalyzeResponse.source` 不新增向量字段。

验证：

- `py -3 -m pytest backend/tests/test_vector_retrieval.py backend/tests/test_retrieval_scoring.py backend/tests/test_retrieval_tools.py`，17 passed。
- `npm run backend:test`，101 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- deterministic embedding 只适合本地 fallback，真实召回质量依赖真实 embedding provider。
- 如果没有先运行 `sync_embeddings.py`，pgvector 候选为空，系统会退回文本检索。
- SQL Memory 的 `question_embedding` / `sql_embedding` 尚未接入混合检索。
