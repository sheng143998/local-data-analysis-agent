# Agent 工作流说明

## API 入口

用户通过：

```http
POST /api/analyze
```

请求体：

```json
{"question":"最近 30 天销售额按天变化如何？"}
```

返回 `AnalyzeResponse`，包含：

- `summary`
- `sql`
- `metrics`
- `rows`
- `source`
- `trace`
- `steps`

## 当前工作流

`backend/app/agents/analysis_graph.py` 是 V1 主链路。

1. 读取用户问题。
2. `build_retrieval_context()` 召回指标口径和 schema。
3. `retrieve_sql_memory()` 检索历史成功 SQL。
4. `plan_sql_reuse()` 决定 `fast_path`、`rewrite_path` 或 `cold_path`。
5. `_select_generated_sql()` 选择 SQL：
   - 默认走确定性 SQL 生成/改写。
   - 开启 `MODEL_SQL_GENERATOR_ENABLED=true` 且 `cold_path` 时尝试模型 SQL 生成。
   - 模型失败或无 SQL 时回退确定性路径。
6. `guard_sql()` 做 SQL 安全拦截。
7. `execute_guarded_sql()` 用只读连接执行。
8. `present_sales_trend_result()` 组织业务结果。
9. `QueryRunLogger` 写入 `query_runs` 和 `tool_calls`。
10. 成功查询写入或更新 SQL Memory。

## 路径含义

- `fast_path`：历史成功 SQL 可直接复用或参数化复用。
- `rewrite_path`：候选相似但不应直接复用，需要改写或重新生成。
- `cold_path`：没有可用历史 SQL，需要新生成。

## 模型路径边界

模型路径目前是可选能力：

```env
MODEL_SQL_GENERATOR_ENABLED=false
```

默认关闭。开启后只影响 `cold_path`，并且生成 SQL 仍然进入 Guard 和 Executor。

## 日志与追踪

每次 `/api/analyze` 会写入：

- `query_runs`：问题、SQL、Guard 状态、执行状态、耗时、错误。
- `tool_calls`：SQL Memory、上下文召回、SQL 生成、Guard、Executor、Presenter、Memory 更新等摘要。

开发者接口：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/memories`
- `GET /api/memories/{memory_id}`

普通用户界面不展示原始工具 payload。
