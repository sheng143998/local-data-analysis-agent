# 统一检索评分基础层计划

## Goal

本模块为 schema、metric、SQL Memory 检索抽出统一评分工具，减少各处手写文本相似、关键词命中、集合重合逻辑。它不新增固定 SQL 模板，而是为后续 embedding / pgvector / pg_trgm 混合检索打基础。

## Current task

当前正在做：验证已通过，准备提交并推送。

## Scope

包含：

- 新增统一检索评分工具：
  - 文本归一化。
  - 文档文本拼接。
  - 文本相似度。
  - 关键词命中分。
  - 集合重合分。
  - 加权评分。
- `metric_retriever.py` 复用共享评分工具。
- `schema_retriever.py` 增加字段级 score，并基于问题、指标必需字段、字段说明排序。
- `sql_memory_tools.py` 复用共享文本相似度和集合重合分。
- 增加 focused tests。
- 更新 README、handoff、模块完成说明。

不包含：

- 不调用外部 embedding 模型。
- 不写入真实向量。
- 不修改数据库 schema。
- 不新增 SQL 模板。
- 不改变普通用户前端可见信息。

## Module boundary

上游输入：

- 用户问题。
- `metric_definitions`。
- `schema_metadata`。
- `sql_memories`。

下游输出：

- metric 召回的 `score`。
- schema 字段召回排序。
- SQL Memory 候选分中的 `text_similarity`、`metric_table_match`。

预计触达文件：

- `backend/app/tools/retrieval_scoring.py`
- `backend/app/tools/metric_retriever.py`
- `backend/app/tools/schema_retriever.py`
- `backend/app/tools/sql_memory_tools.py`
- `backend/app/schemas/retrieval.py`
- `backend/tests/test_retrieval_scoring.py`
- `backend/tests/test_retrieval_tools.py`
- `backend/tests/test_sql_memory_tools.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-unified-retrieval-scoring.md`

## Business logic

当业务人员换问题、换表或增加指标时，系统应该优先通过指标口径、字段说明和历史成功 SQL 的相似性找到相关上下文，而不是依赖固定问法或固定 SQL 模板。本模块让检索评分更可复用、可测试、可替换。

## Data contract

新增内部工具函数：

- `normalize_search_text(text: str) -> str`
- `build_search_document(parts: Iterable[str | None]) -> str`
- `text_similarity(left: str, right: str) -> float`
- `keyword_hit_score(text: str, keywords: Iterable[str]) -> float`
- `overlap_score(left: Collection[str], right: Collection[str]) -> float`
- `weighted_score(components: Mapping[str, tuple[float, float]]) -> float`

`SchemaColumnContext` 新增内部评分字段：

- `score: float = 0`

## Implementation steps

- [x] 读取 handoff 和当前检索代码。
- [x] 新增统一评分工具并接入三个检索模块。
- [x] 增加测试。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`

本模块只改后端检索基础逻辑和文档，不改前端页面；前端构建作为回归检查。

## Risks and open questions

- 当前仍是确定性文本评分，不是真实语义 embedding。
- schema 字段排序可能影响 SQL Generator prompt 的字段顺序，需要后端测试和 e2e 验证。
- 后续接 embedding 时，应保留这些确定性分数作为 fallback 和解释性特征。
