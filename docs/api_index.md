# 接口文档索引与阅读顺序

本文档是 V1 接口文档体系的入口。它说明每份接口文档解决什么问题、适合谁读、何时需要更新。

## 推荐阅读顺序

### 第一次了解当前 API

1. [V1 接口文档](api.md)
2. [前后端接口映射文档](api_frontend_mapping.md)
3. [接口联调与 Smoke 示例文档](api_smoke_examples.md)

适合角色：

- 新加入的前端开发。
- 新加入的后端开发。
- 需要快速理解当前接口范围的测试人员。

### 前端联调

1. [前后端接口映射文档](api_frontend_mapping.md)
2. [接口联调与 Smoke 示例文档](api_smoke_examples.md)
3. [接口错误码与权限边界文档](api_error_auth.md)

重点关注：

- 前端 API client 调用哪些后端接口。
- TypeScript 类型是否覆盖后端响应字段。
- 前端当前是否展示后端 `detail`。
- `/api/runs` 和 `/api/memories` 是否应该进入普通用户页面。

### 后端改接口

1. [接口变更流程与版本维护文档](api_change_process.md)
2. [V1 接口文档](api.md)
3. [接口错误码与权限边界文档](api_error_auth.md)
4. [前后端接口映射文档](api_frontend_mapping.md)

重点关注：

- 这是兼容变更还是破坏性变更。
- 是否修改了 Pydantic schema。
- 前端类型是否需要同步。
- README、handoff 和模块说明是否同步。

### 提交前验证

1. [接口联调与 Smoke 示例文档](api_smoke_examples.md)
2. [接口变更流程与版本维护文档](api_change_process.md)

重点关注：

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`
- 如果涉及 `/api/analyze` 语义，还要运行 `npm run eval:standard`

### 上线或多人试用前审查

1. [接口错误码与权限边界文档](api_error_auth.md)
2. [接口变更流程与版本维护文档](api_change_process.md)
3. [V1 接口文档](api.md)

重点关注：

- 是否需要登录鉴权。
- `/api/runs` 和 `/api/memories` 是否只允许开发者访问。
- 错误信息是否会暴露敏感 SQL、表字段或数据库细节。
- 前端是否能展示清晰的中文错误。

## 文档职责表

| 文档 | 主要用途 | 何时更新 |
| --- | --- | --- |
| [V1 接口文档](api.md) | 说明后端已实现接口的请求、响应、字段和错误。 | 新增接口、修改字段、修改响应结构。 |
| [前后端接口映射文档](api_frontend_mapping.md) | 说明前端 API client、TypeScript 类型和后端接口的映射。 | 前端调用、类型或页面使用字段变化。 |
| [接口错误码与权限边界文档](api_error_auth.md) | 说明错误响应、状态码、权限边界和上线前鉴权建议。 | 错误码、鉴权、调试接口可见性变化。 |
| [接口变更流程与版本维护文档](api_change_process.md) | 说明接口变更分类、同步清单、验证门槛和版本策略。 | 接口变更流程、版本策略或验证规则变化。 |
| [接口联调与 Smoke 示例文档](api_smoke_examples.md) | 说明本地启动、PowerShell/curl 调用示例和 smoke 检查点。 | 端口、启动命令、smoke 脚本或接口示例变化。 |

## 当前接口文档覆盖范围

当前文档已覆盖：

- `GET /api/health`
- `POST /api/analyze`
- `GET /api/metrics`
- `GET /api/metrics/{metric_id}`
- `POST /api/metrics`
- `PUT /api/metrics/{metric_id}`
- `DELETE /api/metrics/{metric_id}`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/memories`
- `GET /api/memories/{memory_id}`

当前文档也覆盖：

- 普通业务接口和开发者调试接口分层。
- 前后端字段映射。
- 错误码和权限边界。
- 接口变更流程。
- 本地 smoke 和手工联调命令。

## 当前文档不代表的内容

这些接口文档只描述当前 V1 已实现或已明确的接口边界，不代表：

- 已经实现登录鉴权。
- 已经实现 `/api/v1` 路径版本。
- 已经把 `/api/runs` 和 `/api/memories` 放入普通用户页面。
- 已经把 `/api/analyze.rows` 泛化为任意表格结构。
- 已经接入真实模型 SQL 生成作为默认路径。

## 维护规则

每次接口相关变更后至少检查：

- README 是否需要新增或调整入口。
- `docs/api.md` 是否需要更新字段。
- `docs/api_frontend_mapping.md` 是否需要更新前端映射。
- `docs/api_error_auth.md` 是否需要更新错误或权限说明。
- `docs/api_change_process.md` 是否需要更新变更规则。
- `docs/api_smoke_examples.md` 是否需要更新联调示例。
- `docs/handoff/current.md` 是否记录当前模块状态。
- `docs/modules/` 是否新增模块完成说明。

## 后续可补充

- 自动生成 OpenAPI 文档入口。
- OpenAPI diff 或契约检查流程。
- 开发者调试页接口文档。
- 登录鉴权后的 `401`、`403` 示例。
- 通用表格响应结构的迁移说明。
