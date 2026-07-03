# 接口变更流程与版本维护文档

本文档说明 V1 API 契约变化时应该如何分类、同步、验证、记录和回滚。它是 [V1 接口文档](api.md)、[前后端接口映射文档](api_frontend_mapping.md) 与 [接口错误码与权限边界文档](api_error_auth.md) 的补充。

## 当前版本策略

当前 API 统一挂载在：

```text
/api
```

当前 FastAPI 应用版本来自：

```text
backend/app/core/config.py -> settings.app_version
```

当前版本：`0.1.0`

V1 阶段暂不引入 `/api/v1` 路径。后续如果需要面向多人、外部系统或长期兼容，应单独设计 `/api/v1`、`/api/v2` 或 header 版本策略。

## 变更分类

### 兼容变更

兼容变更通常不破坏现有前端调用：

- 响应中新增可选字段。
- 新增接口。
- 新增 query 参数且有默认值。
- 新增枚举值，但前端已有兜底展示。
- 错误响应增加额外说明字段，同时保留原 `detail`。
- 文档补充字段说明，不改变字段含义。

兼容变更要求：

- 更新 `docs/api.md`。
- 如前端会使用新字段，更新 `docs/api_frontend_mapping.md`。
- 如涉及错误或权限，更新 `docs/api_error_auth.md`。
- 至少运行相关测试和构建。

### 破坏性变更

破坏性变更会影响现有前端或调用方：

- 修改接口路径。
- 删除字段。
- 修改字段名。
- 修改字段类型。
- 修改必填字段。
- 修改枚举值含义。
- 修改 `rows` 这类核心响应结构。
- 把普通业务接口改为需要鉴权。
- 把开发者调试接口暴露给普通用户导航。
- 改变错误响应结构，例如不再返回 `detail`。

破坏性变更要求：

- 先写计划文档，明确迁移策略。
- 同步后端 schema、前端类型、前端 API client、测试和全部相关文档。
- 在模块完成说明里写清楚兼容影响。
- 运行完整验证命令。
- 如可能，保留旧字段一段时间或提供兼容层。

## API 变更同步清单

每次修改 API 契约时，按以下顺序检查：

| 区域 | 文件 | 必查原因 |
| --- | --- | --- |
| 后端路由 | `backend/app/api/*.py` | 路径、方法、query 参数、path 参数、response_model。 |
| 后端 schema | `backend/app/schemas/*.py` | 请求体、响应体、枚举、字段默认值和校验。 |
| 后端服务 | `backend/app/services/*.py` | 404、业务错误、权限边界和返回对象。 |
| 前端 API client | `frontend/src/api/*.ts` | 请求路径、请求体、错误处理和返回类型。 |
| 前端类型 | `frontend/src/types/*.ts` | TypeScript 字段、枚举、可选性和时间字段类型。 |
| 接口总文档 | `docs/api.md` | 字段说明、示例、错误边界。 |
| 前后端映射 | `docs/api_frontend_mapping.md` | 页面、client 函数、后端接口和字段使用关系。 |
| 错误权限文档 | `docs/api_error_auth.md` | 状态码、鉴权、调试接口权限边界。 |
| README | `README.md` | 文档入口和 API 能力摘要。 |
| Handoff | `docs/handoff/current.md` | 当前状态、风险和下一步。 |
| 模块说明 | `docs/modules/*.md` | 本轮变更、数据契约、验证和风险。 |

## 文档更新规则

### 新增接口

需要更新：

- `docs/api.md`：新增接口用途、请求、响应和错误。
- `docs/api_frontend_mapping.md`：如果前端会调用，增加页面和 client 映射。
- `README.md`：如果是主要能力，加入 API 入口列表。
- `docs/handoff/current.md`：记录模块状态。

### 修改请求字段

需要更新：

- 后端 Pydantic schema。
- 前端 `MetricPayload`、`AnalysisResponse` 或对应类型。
- `docs/api.md` 的请求字段表。
- `docs/api_frontend_mapping.md` 的字段映射。
- 相关测试。

### 修改响应字段

需要更新：

- 后端 response model。
- 前端类型。
- 页面展示逻辑对应说明。
- `docs/api.md` 响应字段表。
- `docs/api_frontend_mapping.md` 后端字段使用情况。

### 修改错误或权限

需要更新：

- `docs/api_error_auth.md`。
- 前端错误处理说明。
- 如新增 `401` 或 `403`，说明触发条件、前端跳转或提示策略。
- 如开发者接口进入前端页面，明确普通用户是否可见。

## 验证门槛

文档类接口变更至少运行：

```bash
npm run backend:test
npm run frontend:build
npm run test:e2e
```

如果变更涉及标准问题评估、SQL 生成或 `/api/analyze` 语义，还应运行：

```bash
npm run eval:standard
```

验证结果需要写入：

- 本轮模块完成说明。
- `docs/handoff/current.md`。
- 最终回复。

## 推荐提交粒度

一次接口文档模块应只解决一个主题：

- 接口总文档。
- 前后端映射。
- 错误码与权限边界。
- 版本和变更流程。
- 某个新增接口的契约说明。

不要把功能实现、接口文档和无关重构混在同一个提交里。

## 回滚与兼容记录

如果接口字段已经被前端使用，回滚或修改时必须记录：

- 旧字段名。
- 新字段名。
- 是否保留兼容字段。
- 前端哪个页面或组件受影响。
- 哪些测试覆盖该字段。
- 文档更新位置。

建议格式：

```text
变更：AnalysisResponse.rows 从固定结构调整为通用表格结构
旧字段：date, amount, orders, avg, refundRate
新字段：Record<string, string | number | null>[]
影响：ChatPage 表格和图表
兼容：保留旧字段到下一次主版本变更
验证：backend:test, frontend:build, test:e2e, eval:standard
```

## 当前已知接口演进点

- `/api/analyze` 的 `rows` 当前仍是固定分析行结构，未来可能需要通用表格结构。
- 前端 `AnalysisResponse` 当前未声明后端返回的 `trace` 和 `steps`。
- 前端 API client 当前没有统一 `client.ts`。
- `/api/runs` 和 `/api/memories` 当前没有鉴权，未来多人使用前需要权限策略。
- 当前没有 `/api/v1` 路径版本，后续如对外提供 API 需要重新评估。

## 当前不做

本阶段只补文档，不做：

- 不新增 `/api/v1`。
- 不修改接口字段。
- 不修改前端类型。
- 不修改错误处理实现。
- 不新增鉴权。
- 不引入 OpenAPI diff 工具。
