# 接口错误码与权限边界文档计划

当前正在做：错误码与权限边界文档已补齐且验证通过，准备提交并推送。

## Goal

在已有 `docs/api.md` 和 `docs/api_frontend_mapping.md` 基础上，补充接口错误响应、前端错误处理现状、开发者调试接口权限边界和上线前鉴权建议，便于后续联调和上线前审查。

## Scope

- 包含：
  - 新增 `docs/api_error_auth.md`。
  - 更新 README、`docs/api.md`、`docs/api_frontend_mapping.md` 的入口。
  - 更新 handoff 和模块完成说明。
- 不包含：
  - 修改后端错误处理实现。
  - 新增鉴权逻辑。
  - 修改前端错误展示。
  - 新增接口或功能代码。

## Module Boundary

- 上游输入：
  - `backend/app/services/*.py`
  - `backend/tests/*.py`
  - `frontend/src/api/*.ts`
  - `docs/api.md`
  - `docs/api_frontend_mapping.md`
- 输出：
  - 中文错误码和权限边界文档。

## Business Logic

- 当前普通业务接口无登录鉴权，适合本地单机开发。
- `/api/runs` 和 `/api/memories` 暴露运行记录和 SQL Memory，应视为开发者调试接口。
- 文档需要明确当前已知错误：`404`、`422`、前端 `response.ok` 通用错误，以及数据库或运行时异常的现状。

## Data Contract

本模块不改变数据契约，只记录当前错误响应格式：

```json
{
  "detail": "错误说明"
}
```

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 梳理现有错误响应和权限现状。
- [x] 编写错误码与权限边界文档。
- [x] 更新 README、接口文档、映射文档、handoff 和模块完成说明。
- [x] 运行验证命令。
- [x] 提交并推送。

## Validation Plan

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and Open Questions

- 当前只是文档，不实现鉴权。
- 如果后续增加登录、角色或 API token，需要同步更新本文档和前端错误处理策略。
