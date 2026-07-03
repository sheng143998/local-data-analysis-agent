# 接口联调与 Smoke 示例文档计划

当前正在做：接口联调与 smoke 示例文档已补齐且验证通过，准备提交并推送。

## Goal

在已有 API 契约文档基础上，提供一份可操作的中文联调说明，让开发者或测试人员能快速启动服务、调用关键接口、理解 `npm run test:e2e` 检查了什么。

## Scope

- 包含：
  - 新增 `docs/api_smoke_examples.md`。
  - 更新 README 和相关 API 文档入口。
  - 更新 handoff 和模块完成说明。
- 不包含：
  - 修改 smoke 脚本。
  - 修改后端接口。
  - 修改前端 API client。
  - 新增测试代码。

## Module Boundary

- 上游输入：
  - `package.json`
  - `backend/tests/smoke_api.py`
  - `docs/api.md`
  - `README.md`
- 输出：
  - 中文接口联调与 smoke 示例文档。

## Business Logic

- 文档说明如何用本地命令验证 API 可用性。
- 文档明确 smoke 检查点是健康检查和一次真实 `/api/analyze` 链路，而不是完整语义评估。
- 文档区分手工联调、后端测试、E2E smoke 和标准问题评估。

## Data Contract

本模块不改变接口契约，只记录当前调用示例：

- `GET /api/health`
- `POST /api/analyze`
- `GET/POST/PUT/DELETE /api/metrics`
- `GET /api/runs`
- `GET /api/memories`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 梳理 smoke 脚本和项目脚本。
- [x] 编写接口联调与 smoke 示例文档。
- [x] 更新 README、接口文档入口、handoff 和模块完成说明。
- [x] 运行验证命令。
- [x] 提交并推送。

## Validation Plan

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and Open Questions

- 文档示例假设后端运行在 `http://localhost:8000`。
- 如果后续统一 API client、增加鉴权或修改端口，需要同步更新本文档。
