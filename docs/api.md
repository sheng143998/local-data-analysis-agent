# V1 接口文档

本文档说明当前 FastAPI 已实现的 V1 接口。所有接口默认挂载在 `/api` 前缀下。阅读顺序见 [接口文档索引与阅读顺序](api_index.md)，前端 API client 与后端接口字段关系见 [前后端接口映射文档](api_frontend_mapping.md)，错误码和权限边界见 [接口错误码与权限边界文档](api_error_auth.md)，字段或路径变更流程见 [接口变更流程与版本维护文档](api_change_process.md)，手工联调命令见 [接口联调与 Smoke 示例文档](api_smoke_examples.md)。

## 接口分层

### 普通业务接口

普通业务接口可以被前端业务页面直接使用：

- `GET /api/health`
- `POST /api/analyze`
- `GET /api/metrics`
- `GET /api/metrics/{metric_id}`
- `POST /api/metrics`
- `PUT /api/metrics/{metric_id}`
- `DELETE /api/metrics/{metric_id}`

### 开发者调试接口

以下接口用于调试、排查和评估，不进入普通用户主导航：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/memories`
- `GET /api/memories/{memory_id}`

普通用户界面不默认展示模型状态、数据库连接状态、SQL Memory 候选分数、prompt、工具调用原始 payload 或评估报告。

## 通用约定

- 请求和响应均使用 JSON。
- 时间字段使用 ISO 8601 字符串。
- `UUID` 字段使用标准 UUID 字符串。
- 当前没有登录鉴权层，后续如果增加用户系统，需要同步补充鉴权头和权限错误说明。
- 后端常见错误响应遵循 FastAPI 默认格式：

```json
{
  "detail": "错误说明"
}
```

## 健康检查

### `GET /api/health`

用途：检查后端服务是否可用。

请求参数：无。

响应示例：

```json
{
  "ok": true,
  "service": "local-data-analysis-agent",
  "version": "0.1.0"
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `ok` | boolean | 服务是否可用。 |
| `service` | string | 服务标识。 |
| `version` | string | 当前 API 版本。 |

## 数据问答

### `POST /api/analyze`

用途：用户用自然语言提出业务问题，后端完成上下文召回、SQL Memory 检索、SQL 生成或复用、SQL Guard、只读执行和结果整理。

请求体：

```json
{
  "question": "最近 30 天销售额按天变化如何？"
}
```

请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `question` | string | 是 | 用户输入的中文业务问题。当前 schema 默认允许空字符串，但业务上应传入明确问题。 |

响应示例：

```json
{
  "question": "最近 30 天销售额按天变化如何？",
  "path": "fast_path",
  "summary": "基于真实 PostgreSQL 数据，最近 30 天销售额...",
  "sql": "SELECT ...",
  "metrics": [
    {
      "label": "销售额",
      "value": "12345",
      "delta": "0%",
      "hint": "已支付订单金额汇总"
    }
  ],
  "rows": [
    {
      "order_date": "2026-06-01",
      "daily_sales": 1000.0,
      "order_count": 20,
      "avg_order_value": 50.0,
      "refund_rate": 0.0
    }
  ],
  "source": {
    "dataset": "Olist 巴西电商公开数据集 + 合成增强数据",
    "tables": ["orders", "payments"],
    "fields": ["orders.created_at", "orders.total_amount"],
    "metricDefinition": "销售额 = 已支付订单金额汇总",
    "range": "最近 30 个有交易日期",
    "returnedRows": 30,
    "queryTime": "120ms",
    "security": "SQL Guard 已通过，只读 SELECT"
  },
  "trace": {
    "toolCalls": 8,
    "modelCalls": 0,
    "memoryCandidates": 3,
    "totalTime": "300ms"
  },
  "steps": [
    {
      "name": "检索 SQL Memory",
      "status": "已完成",
      "time": "10ms"
    }
  ]
}
```

响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `question` | string | 原始用户问题。 |
| `path` | string | Agent 路径：`fast_path`、`rewrite_path` 或 `cold_path`。 |
| `summary` | string | 面向业务用户的中文分析结论。 |
| `sql` | string | 最终执行或准备执行的 SQL。 |
| `metrics` | array | 指标摘要卡片。 |
| `rows` | array | 结果表数据。当前为通用行结构，字段来自最终 SQL 执行结果，例如 `order_date`、`daily_sales`、`order_count`。 |
| `source` | object | 数据来源、表字段、指标口径、返回行数、耗时和安全说明。 |
| `trace` | object | 简化追踪信息。普通用户界面可选择弱化展示，不展示原始工具 payload。 |
| `steps` | array | Agent 执行步骤摘要。 |

`path` 取值说明：

| 值 | 说明 |
| --- | --- |
| `fast_path` | 高置信 SQL Memory 复用。 |
| `rewrite_path` | 相似 SQL 需要改写或重新生成。 |
| `cold_path` | 没有可用记忆，需要从召回上下文生成 SQL。 |

注意：

- 模型 SQL 生成默认由 `MODEL_SQL_GENERATOR_ENABLED=false` 关闭。
- 即使开启模型路径，生成 SQL 也必须经过 SQL Guard 和只读 Executor。
- 内部 SQL Memory 分数、prompt、模型原始输出和工具调用原始 payload 不属于普通用户接口展示内容。
- `rows` 不再固定为销售趋势字段；前端应按返回行的 key 动态生成表头，避免换表或新增查询列后无法展示。

## 指标口径

指标口径是业务资产，用于让系统理解“销售额、订单数、退款率、客单价”等指标定义。

### MetricDefinition 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID | 指标 ID。 |
| `metric_name` | string | 机器可读指标名，例如 `sales_amount`。 |
| `display_name` | string | 中文展示名，例如 `销售额`。 |
| `description` | string | 指标说明。 |
| `formula` | string | 指标公式或 SQL 口径说明。 |
| `required_tables` | string[] | 计算该指标依赖的数据表。 |
| `required_fields` | string[] | 计算该指标依赖的字段。 |
| `default_filters` | object | 默认过滤条件。 |
| `example_question` | string | 示例问题。 |
| `owner` | string | 负责人或业务归属。 |
| `status` | string | `enabled`、`draft` 或 `disabled`。 |
| `created_at` | datetime | 创建时间。 |
| `updated_at` | datetime | 更新时间。 |

### `GET /api/metrics`

用途：获取指标口径列表。

响应：`MetricDefinition[]`。

### `GET /api/metrics/{metric_id}`

用途：根据 ID 获取单个指标口径。

路径参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `metric_id` | UUID | 指标 ID。 |

成功响应：`MetricDefinition`。

错误：

| 状态码 | 说明 |
| --- | --- |
| `404` | 指标不存在。 |

### `POST /api/metrics`

用途：创建指标口径。

请求体示例：

```json
{
  "metric_name": "gross_margin_rate",
  "display_name": "毛利率",
  "description": "毛利额占销售额的比例",
  "formula": "(sales_amount - cost_amount) / sales_amount",
  "required_tables": ["order_items", "product_costs", "payments"],
  "required_fields": ["order_items.price", "product_costs.unit_cost", "payments.status"],
  "default_filters": {
    "payments.status": "paid"
  },
  "example_question": "最近 30 天毛利率最高的商品品类是什么？",
  "owner": "经营分析组",
  "status": "enabled"
}
```

必填字段：

- `metric_name`
- `display_name`
- `description`
- `formula`

成功响应：创建后的 `MetricDefinition`。

校验错误：

| 状态码 | 说明 |
| --- | --- |
| `422` | 请求字段类型不正确，或必填字符串为空。 |

### `PUT /api/metrics/{metric_id}`

用途：更新指标口径。请求体支持部分字段更新。

请求体示例：

```json
{
  "display_name": "毛利率",
  "status": "enabled"
}
```

成功响应：更新后的 `MetricDefinition`。

错误：

| 状态码 | 说明 |
| --- | --- |
| `404` | 指标不存在。 |
| `422` | 请求字段类型不正确。 |

### `DELETE /api/metrics/{metric_id}`

用途：删除指标口径。

成功响应：

```json
{
  "deleted": true
}
```

错误：

| 状态码 | 说明 |
| --- | --- |
| `404` | 指标不存在。 |

## 运行记录调试接口

运行记录接口用于开发者查看 `/api/analyze` 的执行摘要和工具调用记录。

### QueryRunRecord 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID | 运行记录 ID。 |
| `user_question` | string | 用户问题。 |
| `rewritten_question` | string/null | 改写后的问题，当前可为空。 |
| `memory_hit` | boolean | 是否命中 SQL Memory fast path。 |
| `memory_id` | UUID/null | 命中的 SQL Memory ID。 |
| `generated_sql` | string/null | 生成或复用的 SQL。 |
| `final_sql` | string/null | Guard 后最终 SQL。 |
| `guard_status` | string | Guard 状态。 |
| `execution_status` | string | SQL 执行状态。 |
| `row_count` | number | 返回行数。 |
| `latency_ms` | number | 总耗时，单位毫秒。 |
| `error_message` | string/null | 错误信息。 |
| `created_at` | datetime | 创建时间。 |

### ToolCallRecord 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID | 工具调用 ID。 |
| `query_run_id` | UUID/null | 所属运行记录 ID。 |
| `tool_name` | string | 工具名。 |
| `input_payload` | object | 输入摘要。 |
| `output_payload` | object | 输出摘要。 |
| `status` | string | 工具调用状态。 |
| `latency_ms` | number | 工具耗时，单位毫秒。 |
| `error_message` | string/null | 错误信息。 |
| `created_at` | datetime | 创建时间。 |

当前关键工具的 `output_payload` 摘要包括：

| 工具 | 典型字段 | 说明 |
| --- | --- | --- |
| `context_builder.build_retrieval_context` | `metric_count`, `schema_column_count`, `relationship_count`, `tables`, `fields_sample` | 本次上下文召回规模和字段样例。 |
| `analysis_graph.select_generated_sql` | `generation_path`, `has_sql`, `warning_count`, `warnings` | SQL 生成路径和 warning 摘要。 |
| `sql_validation_tools.guard_sql` | `guard_status`, `warning_count`, `warnings`, `error_count`, `errors` | SQL Guard 放行状态和诊断摘要。 |

### `GET /api/runs`

用途：查看最近运行记录。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `limit` | number | `20` | 返回数量。后端会限制到 1 到 100 之间。 |

响应：`QueryRunRecord[]`。

### `GET /api/runs/{run_id}`

用途：查看单次运行记录和工具调用明细。

成功响应：`QueryRunDetail`，字段包含 `QueryRunRecord` 的全部字段，并额外包含：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `tool_calls` | ToolCallRecord[] | 本次运行的工具调用列表。 |

错误：

| 状态码 | 说明 |
| --- | --- |
| `404` | 运行记录不存在。 |

## SQL Memory 调试接口

SQL Memory 接口用于开发者查看历史成功 SQL 记忆，不进入普通用户主导航。

### SqlMemoryRecord 字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID | SQL Memory ID。 |
| `canonical_question` | string | 标准问题。 |
| `normalized_question` | string | 归一化问题。 |
| `question_pattern` | string | 问题模式，当前可为空。 |
| `intent` | string | 意图，当前可为空。 |
| `sql_template` | string | SQL 模板。 |
| `final_sql` | string | 最近成功执行的最终 SQL。 |
| `param_schema` | object | 参数 schema。 |
| `parameters` | object | 当前记忆保存的参数。 |
| `tables` | string[] | SQL 涉及表。 |
| `metrics` | string[] | 涉及指标。 |
| `dimensions` | string[] | 分析维度。 |
| `filters` | object | 过滤条件。 |
| `dialect` | string | SQL 方言，当前为 `postgresql`。 |
| `schema_version` | string | schema 版本。 |
| `success_count` | number | 成功复用次数。 |
| `failure_count` | number | 失败次数。 |
| `avg_latency_ms` | number | 平均耗时。 |
| `last_result_columns` | string[] | 最近结果列。 |
| `last_row_count` | number | 最近返回行数。 |
| `last_used_at` | datetime/null | 最近使用时间。 |
| `created_at` | datetime | 创建时间。 |

### `GET /api/memories`

用途：查看 SQL Memory 列表。

查询参数：

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `limit` | number | `50` | 返回数量。后端会限制到 1 到 100 之间。 |

响应：`SqlMemoryRecord[]`。

### `GET /api/memories/{memory_id}`

用途：查看单条 SQL Memory。

成功响应：`SqlMemoryRecord`。

错误：

| 状态码 | 说明 |
| --- | --- |
| `404` | SQL Memory 不存在。 |

## 当前接口风险

- `/api/analyze` 当前 `rows` 已使用通用表格结构，但自然语言总结仍主要围绕 V1 已覆盖的销售、订单、退款率、毛利率、复购率和客单价指标。
- `/api/runs` 和 `/api/memories` 是开发者调试接口，暂未加鉴权；上线或多人使用前需要增加权限控制。
- 当前测试直接连接本地数据库，后续需要独立测试库和测试数据隔离。
