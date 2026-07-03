# SQL Memory 机制说明

## 目标

SQL Memory 用于复用历史成功 SQL，提升高频相似问题的响应速度，同时保留 Guard 和只读执行安全链路。

## 存储表

表：`sql_memories`

关键字段：

- `canonical_question`
- `normalized_question`
- `sql_template`
- `final_sql`
- `question_embedding`
- `sql_embedding`
- `parameters`
- `tables`
- `metrics`
- `dimensions`
- `success_count`
- `failure_count`
- `avg_latency_ms`
- `last_result_columns`
- `last_row_count`

## 检索与打分

实现文件：

```text
backend/app/tools/sql_memory_tools.py
```

当前打分：

```text
score = 0.45 * semantic_similarity
      + 0.25 * text_similarity
      + 0.20 * metric_table_match
      + 0.10 * success_score
```

当前 `semantic_similarity` 优先来自 `sql_memories.question_embedding` 的 pgvector 语义候选分；如果 embedding 调用失败、历史 memory 尚未写入向量或 pgvector 查询不可用，则回退为文本相似度。

阈值：

- `score >= 0.88`：候选可进入 `fast_path`，但还要满足关键表约束。
- `0.70 <= score < 0.88`：`rewrite_path`。
- `< 0.70`：`cold_path`。

## fast_path 关键表约束

为了避免相似文本错误复用，V1 已增加关键表约束：

- 用户类问题需要 `users`。
- 访问、加购、流量来源、转化率问题需要 `traffic_events`。
- 优惠券、核销问题需要 `coupon_usages`，部分问题还需要 `coupons`。

候选 SQL 缺少关键表时，即使得分高，也不能进入 `fast_path`，会降级到 `rewrite_path`。

## 写入条件

当前 `/api/analyze` 成功执行且 Guard 放行后，会调用 `upsert_successful_sql_memory()` 写入或更新 SQL Memory。

写入内容包括：

- 问题。
- SQL 模板。
- 最终 SQL。
- 问题 embedding。
- SQL embedding。
- 参数。
- 表和指标。
- 结果列和行数。
- 执行耗时。

## 历史向量补齐

新写入的 SQL Memory 会自动带上 question/sql embedding。旧记录如果缺少向量，可运行：

```bash
py -3 backend/scripts/sync_embeddings.py --target memory
```

脚本只扫描 `question_embedding IS NULL OR sql_embedding IS NULL` 的历史 memory，生成并回写两个向量。默认 `--target all` 也会包含 memory 补齐。

## 开发者接口

- `GET /api/memories`
- `GET /api/memories/{memory_id}`

普通用户界面不展示 SQL Memory 候选分数或内部路径评分。

## 已知边界

- 已接入 question/sql embedding 写入和 question_embedding pgvector 召回；旧记录若没有向量会回退文本相似。
- 历史 memory 可以用 `sync_embeddings.py --target memory` 补齐向量。
- fast_path 约束目前是关键词启发式。
- 严格评估显示仍有部分问题需要模型 SQL 生成或更强意图生成修复。
