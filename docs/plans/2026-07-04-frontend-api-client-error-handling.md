# 统一前端 API Client 与错误解析计划

## Goal

本模块解决前端 API 调用分散、错误提示粗糙的问题。后续换库、换表或扩展接口时，前端可以复用统一请求入口，而不是在每个业务 client 中重复 `fetch`、base URL、JSON 解析和错误处理。

## Current task

当前正在做：验证已通过，准备提交并推送。

## Scope

包含：

- 新增统一前端 API client。
- 解析 FastAPI `detail`，转换为中文、业务用户可理解的错误。
- 保持普通用户页面不展示模型状态、数据库状态、SQL Memory 分数、prompt 或调试 payload。
- 更新前后端接口映射、错误码文档、README、handoff 和模块完成说明。
- 运行前端构建、后端测试和 e2e smoke。

不包含：

- 不新增固定 SQL 模板。
- 不新增模板配置页面。
- 不修改 `/api/analyze` 语义生成逻辑。
- 不实现登录鉴权。
- 不把 `/api/runs`、`/api/memories` 放入普通用户导航。

## Module boundary

上游输入：

- 前端页面和组件调用 `analysisClient.ts`、`metricClient.ts`。
- 后端 FastAPI 返回 JSON 响应或标准错误响应 `{ "detail": ... }`。

下游输出：

- 前端业务 client 返回 typed JSON。
- 请求失败时抛出中文 `ApiError`，页面现有错误展示可以直接使用。

预计触达文件：

- `frontend/src/api/client.ts`
- `frontend/src/api/analysisClient.ts`
- `frontend/src/api/metricClient.ts`
- `docs/api_frontend_mapping.md`
- `docs/api_error_auth.md`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-frontend-api-client-error-handling.md`

## Business logic

业务分析人员只需要看到“分析失败、请检查问题或稍后重试”“指标不存在”“字段填写不完整”等可理解提示。后端返回的技术错误、Pydantic 结构化校验详情或网络异常应在前端统一收敛，不暴露数据库连接串、模型状态、SQL Memory 评分或调试 payload。

## Data contract

统一 client 输入：

- `path`: 以 `/api/...` 开头的接口路径。
- `method`: HTTP 方法，默认 `GET`。
- `body`: 可选 JSON 请求体。
- `fallbackMessage`: 当前业务动作的中文兜底错误。

统一 client 输出：

- 成功时返回 `Promise<T>`。
- 失败时抛出 `ApiError`：
  - `message`: 中文用户可读错误。
  - `status`: HTTP 状态码或 `0` 网络错误。
  - `detail`: 后端原始 `detail` 的安全摘要。

## Implementation steps

- [x] 读取 handoff、接口文档和前端 API client 现状。
- [x] 新增统一 client 并接入问答、指标 CRUD。
- [x] 更新接口映射和错误码文档。
- [x] 更新 README、handoff 和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `npm run frontend:build`
- `npm run backend:test`
- `npm run test:e2e`

本模块不修改 `/api/analyze` SQL 生成语义，暂不强制运行 `npm run eval:standard`。

## Risks and open questions

- 当前页面现有错误展示只读取 `Error.message`，统一 client 需保持兼容。
- FastAPI `detail` 可能是字符串或数组，前端需要对数组做简化摘要。
- 后续实现鉴权时，可在统一 client 增加 token/header 和 `401/403` 分支。
