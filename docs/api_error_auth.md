# 接口错误码与权限边界文档

本文档说明当前 V1 API 的错误响应、前端错误处理现状、接口权限边界和上线前鉴权建议。它是 [V1 接口文档](api.md) 与 [前后端接口映射文档](api_frontend_mapping.md) 的补充。

## 当前结论

- 当前 API 没有登录鉴权层，适合本地单机开发和受控演示环境。
- 普通业务接口和开发者调试接口都挂在 `/api` 下。
- `/api/runs` 和 `/api/memories` 会暴露运行记录、工具调用摘要、SQL 和 SQL Memory，应视为开发者调试接口。
- 前端当前只根据 `response.ok` 抛出中文通用错误，没有解析后端 `detail`。
- 后端错误响应主要使用 FastAPI 默认结构：

```json
{
  "detail": "错误说明"
}
```

## 当前状态码

| 状态码 | 来源 | 当前含义 | 前端现状 |
| --- | --- | --- | --- |
| `200` | FastAPI 路由正常返回 | 请求成功。 | 前端读取 JSON 并渲染页面。 |
| `404` | `MetricService`、`RunService`、`MemoryService` | 指标、运行记录或 SQL Memory 不存在。 | 前端指标 CRUD 当前会抛出通用错误，不展示具体 `detail`。 |
| `422` | FastAPI / Pydantic | 请求体、路径参数或查询参数类型不合法；必填字段不满足校验。 | 前端当前会抛出通用错误。 |
| `500` | 未捕获运行时异常 | 数据库连接、执行链路或其他未处理异常。 | 前端当前会抛出通用错误。 |

## 资源不存在错误

### 指标口径不存在

涉及接口：

- `GET /api/metrics/{metric_id}`
- `PUT /api/metrics/{metric_id}`
- `DELETE /api/metrics/{metric_id}`

当前响应：

```json
{
  "detail": "指标不存在"
}
```

状态码：`404`

### 运行记录不存在

涉及接口：

- `GET /api/runs/{run_id}`

当前响应：

```json
{
  "detail": "运行记录不存在"
}
```

状态码：`404`

### SQL Memory 不存在

涉及接口：

- `GET /api/memories/{memory_id}`

当前响应：

```json
{
  "detail": "SQL Memory 不存在"
}
```

状态码：`404`

## 参数校验错误

FastAPI 和 Pydantic 会自动处理字段类型、UUID 格式和必填字段校验。

典型场景：

- `metric_id` 不是合法 UUID。
- `status` 不是 `enabled`、`draft` 或 `disabled`。
- 创建指标时 `metric_name`、`display_name`、`description` 或 `formula` 为空。
- 请求体不是合法 JSON。

状态码：`422`

响应结构示例：

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "metric_name"],
      "msg": "String should have at least 1 character",
      "input": ""
    }
  ]
}
```

说明：

- `detail` 可能是字符串，也可能是数组。
- 前端当前没有解析 `detail`，只显示通用错误。
- 如果后续要对业务用户展示更友好的校验信息，应在前端 API client 层统一解析。

## 前端错误处理现状

当前文件：

- `frontend/src/api/analysisClient.ts`
- `frontend/src/api/metricClient.ts`

当前策略：

```ts
if (!response.ok) {
  throw new Error('分析接口调用失败');
}
```

指标接口也使用类似通用错误：

- `获取指标列表失败`
- `创建指标失败`
- `更新指标失败`
- `删除指标失败`

当前限制：

- 没有读取后端 `detail`。
- 没有区分 `404`、`422`、`500`。
- 没有统一超时处理。
- 没有统一鉴权失败处理，因为当前尚无鉴权层。

建议后续抽象统一 client：

```text
frontend/src/api/client.ts
```

统一处理：

- base URL。
- JSON 解析。
- FastAPI `detail`。
- 网络异常。
- 鉴权 header。
- `401`、`403`、`404`、`422`、`500` 的中文提示。

## 权限边界

### 普通业务接口

普通业务页面当前使用：

- `POST /api/analyze`
- `GET /api/metrics`
- `POST /api/metrics`
- `PUT /api/metrics/{metric_id}`
- `DELETE /api/metrics/{metric_id}`

当前权限状态：未加登录鉴权。

本地 V1 阶段可接受原因：

- 项目定位是本地数据分析 Agent。
- 当前运行环境是本机开发和测试。
- 数据库连接串只保存在 `backend/.env`，不提交到仓库。

### 开发者调试接口

开发者调试接口：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/memories`
- `GET /api/memories/{memory_id}`

这些接口可能包含：

- 用户问题。
- 最终 SQL。
- 工具调用摘要。
- SQL Memory。
- 表名、字段名和指标名。
- 执行状态、错误和耗时。

当前权限状态：未加登录鉴权，但文档和产品边界已要求不进入普通用户主导航。

上线或多人使用前建议：

- 至少增加开发者开关或角色判断。
- 只允许管理员或开发者角色访问。
- 对 SQL、工具 payload 和错误信息做脱敏策略。
- 限制列表接口的最大返回数量。
- 记录调试接口访问日志。

## 建议的未来错误码

当前未实现，但后续可按以下方向收敛：

| 状态码 | 建议使用场景 |
| --- | --- |
| `400` | 业务参数不合法，但不是 Pydantic 类型错误。 |
| `401` | 未登录或 token 缺失。 |
| `403` | 已登录但无权访问开发者调试接口。 |
| `404` | 资源不存在。 |
| `409` | 创建或更新资源时发生唯一键冲突。 |
| `422` | 请求结构或字段类型校验失败。 |
| `500` | 未预期服务端错误。 |
| `503` | 模型服务、数据库或外部依赖不可用。 |

## 上线前接口检查清单

上线或多人试用前至少检查：

- 是否需要登录鉴权。
- `/api/runs` 和 `/api/memories` 是否仅开发者可见。
- 前端是否能展示后端 `detail` 的中文错误。
- 数据库连接失败时是否返回用户可理解的错误。
- SQL Guard 拦截时是否以业务可理解方式展示。
- 是否需要隐藏或脱敏最终 SQL。
- 是否需要限制单次查询返回行数和超时时间。
- 是否需要记录 API 访问日志。

## 当前不做

V1 当前接口文档阶段不做：

- 不新增登录系统。
- 不实现角色权限。
- 不修改 API 响应结构。
- 不修改前端错误展示。
- 不把开发者调试接口放到普通用户主导航。
