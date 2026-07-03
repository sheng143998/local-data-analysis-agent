# 接口变更流程与版本维护文档计划

当前正在做：接口变更流程与版本维护文档已补齐且验证通过，准备提交并推送。

## Goal

在已有接口文档、前后端映射文档、错误码与权限边界文档基础上，补充接口变更时的中文流程说明，避免后续改动 API 字段、路径、错误响应或权限边界时漏更新前端类型、测试、README 和模块记录。

## Scope

- 包含：
  - 新增 `docs/api_change_process.md`。
  - 更新 README、`docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_error_auth.md` 的入口。
  - 更新 handoff 和模块完成说明。
- 不包含：
  - 修改 API 实现。
  - 修改前端 API client 或 TypeScript 类型。
  - 修改测试代码。
  - 新增接口。

## Module Boundary

- 上游输入：
  - `executable-plan-draft.md`
  - `docs/api.md`
  - `docs/api_frontend_mapping.md`
  - `docs/api_error_auth.md`
  - `README.md`
- 输出：
  - 中文 API 变更流程和版本维护文档。

## Business Logic

- 后续任何 API 字段、路径、错误响应、权限边界或前端映射变化，都必须同步文档和验证。
- 文档应明确“兼容变更”和“破坏性变更”的处理方式。
- V1 当前仍使用 `/api` 前缀和 FastAPI app version，不引入 `/api/v1` 路径改造。

## Data Contract

本模块不改变数据契约，只记录变更流程。涉及的权威契约文件包括：

- `backend/app/api/*.py`
- `backend/app/schemas/*.py`
- `frontend/src/api/*.ts`
- `frontend/src/types/*.ts`
- `docs/api.md`
- `docs/api_frontend_mapping.md`
- `docs/api_error_auth.md`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 梳理草案和现有接口文档。
- [x] 编写接口变更流程与版本维护文档。
- [x] 更新 README、接口文档入口、handoff 和模块完成说明。
- [x] 运行验证命令。
- [x] 提交并推送。

## Validation Plan

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and Open Questions

- 当前只是流程文档，不引入自动 OpenAPI diff 或文档 lint。
- 如果后续改为 `/api/v1` 版本化路径，需要单独做接口迁移方案和兼容策略。
