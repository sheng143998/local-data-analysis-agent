# 模块：统一检索评分基础层

当前状态：代码开发完成，验证已通过，随本次提交完成 commit 和 push，提交信息为 `统一检索评分基础层并通过验证`。

业务逻辑：

本模块把 metric、schema、SQL Memory 检索中分散的文本相似、关键词命中、集合重合和加权求分逻辑统一到一个基础工具中。它不新增固定 SQL 模板，也不调用外部 embedding 服务，而是让当前确定性检索更可测试、更可解释，并为后续 pgvector / embedding 混合检索保留清楚替换点。

关键代码：

- `backend/app/tools/retrieval_scoring.py`：新增 `normalize_search_text()`、`build_search_document()`、`text_similarity()`、`keyword_hit_score()`、`overlap_score()`、`weighted_score()`。
- `backend/app/tools/metric_retriever.py`：指标召回改为复用统一评分工具，分数由名称命中、关键词命中、文本相似和趋势意图组成。
- `backend/app/tools/schema_retriever.py`：字段召回增加字段级 `score`，综合必需字段、相关表、关键词、文本相似和字段优先级排序。
- `backend/app/tools/sql_memory_tools.py`：SQL Memory 检索复用统一 `text_similarity()` 和 `overlap_score()`，原混合公式保持不变。
- `backend/app/schemas/retrieval.py`：`SchemaColumnContext` 增加内部 `score` 字段。

数据契约：

内部评分函数：

```python
normalize_search_text(text)
build_search_document(parts)
text_similarity(left, right)
keyword_hit_score(text, keywords)
overlap_score(left, right)
weighted_score(components)
```

`SchemaColumnContext.score` 仅用于后端召回排序和调试，不进入普通用户页面。

验证：

- `npm run backend:test`：80 passed，1 个 `StarletteDeprecationWarning`，不影响本模块。
- `npm run frontend:build`：已通过。
- `npm run test:e2e`：已通过，question -> FastAPI -> AgentService -> Guard -> Executor -> result。

风险/后续：

- 当前 semantic similarity 仍不是 embedding 语义向量，后续需要接 ModelAdapter/EmbeddingAdapter 或 pgvector 查询。
- schema 字段排序已有 score，但自然语言总结仍主要面向 V1 已覆盖指标。
- 后续可把这些确定性分数作为混合检索中的 fallback 和可解释特征。
