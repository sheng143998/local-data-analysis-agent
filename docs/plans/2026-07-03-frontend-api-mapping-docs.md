# 前后端接口映射文档计划

当前正在做：前后端接口映射文档已补齐且验证通过，准备提交并推送。

## Goal

在已有 `docs/api.md` 的后端接口文档基础上，补齐前端实际调用哪些接口、使用哪些字段、忽略哪些后端调试字段，以及后续接口变更时需要同步哪些文件。

## Scope

- 包含：
  - 新增 `docs/api_frontend_mapping.md`。
  - 更新 README 和 `docs/api.md` 的相关入口。
  - 更新 handoff 和模块完成说明。
- 不包含：
  - 修改前端 API client。
  - 修改 TypeScript 类型。
  - 修改后端接口。
  - 新增接口或功能。

## Module Boundary

- 上游输入：
  - `frontend/src/api/analysisClient.ts`
  - `frontend/src/api/metricClient.ts`
  - `frontend/src/types/analysis.ts`
  - `frontend/src/types/metric.ts`
  - `docs/api.md`
- 输出：
  - 中文前后端接口映射说明。

## Business Logic

- 前端普通用户页面当前只调用数据问答和指标口径接口。
- 开发者调试接口 `/api/runs` 和 `/api/memories` 当前没有前端普通页面入口。
- 文档需要明确 `AnalyzeResponse.trace`、`AnalyzeResponse.steps` 等后端字段当前未进入前端类型，避免后续误以为接口缺失。

## Data Contract

本模块不改变数据契约，只记录现有映射：

- `analyzeQuestion(question)` -> `POST /api/analyze`
- `listMetrics()` -> `GET /api/metrics`
- `createMetric(payload)` -> `POST /api/metrics`
- `updateMetric(id, payload)` -> `PUT /api/metrics/{metric_id}`
- `deleteMetric(id)` -> `DELETE /api/metrics/{metric_id}`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 读取前端 API client 和类型定义。
- [x] 编写前后端接口映射文档。
- [x] 更新 README、`docs/api.md`、handoff 和模块完成说明。
- [x] 运行验证命令。
- [x] 提交并推送。

## Validation Plan

- `npm run frontend:build`
- `npm run backend:test`

## Risks and Open Questions

- 当前前端没有统一 `client.ts`，`analysisClient.ts` 和 `metricClient.ts` 各自维护 `API_BASE_URL`。
- 当前前端 `AnalysisResponse` 类型没有声明后端返回的 `trace` 和 `steps`，运行时不影响页面，但后续如果前端要展示执行步骤，需要同步类型。
