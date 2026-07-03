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

当前 `semantic_similarity` 暂用文本相似度代替，后续会接 pgvector。

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
- 参数。
- 表和指标。
- 结果列和行数。
- 执行耗时。

## 开发者接口

- `GET /api/memories`
- `GET /api/memories/{memory_id}`

普通用户界面不展示 SQL Memory 候选分数或内部路径评分。

## 已知边界

- 尚未接入真实 embedding。
- fast_path 约束目前是关键词启发式。
- 严格评估显示仍有部分问题需要模型 SQL 生成或更强意图生成修复。
