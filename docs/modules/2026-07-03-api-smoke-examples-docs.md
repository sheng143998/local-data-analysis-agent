# 接口联调与 Smoke 示例文档模块完成说明

模块：接口联调与 Smoke 示例文档

当前状态：中文接口联调与 smoke 示例文档已补齐，README 和相关接口文档入口已更新，验证已通过，准备随本次提交推送完成。

业务逻辑：本模块不修改任何接口实现、测试脚本、前端 API client 或数据库结构，只补充本地联调说明。文档说明如何启动后端、用 PowerShell/curl 调用关键接口、理解 `npm run test:e2e` 的检查点，并区分后端测试、前端构建、E2E smoke 和标准问题评估。

关键代码：本模块只涉及文档：

- `docs/api_smoke_examples.md`：新增本地启动、PowerShell/curl 示例、自动 smoke 检查点、验证命令分层和常见问题。
- `README.md`：增加接口联调与 smoke 示例文档入口。
- `docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_error_auth.md`、`docs/api_change_process.md`：互链接口联调文档。
- `docs/plans/2026-07-03-api-smoke-examples-docs.md`：记录本轮文档任务计划和边界。

数据契约：没有新增或修改 API 字段。文档只记录当前示例调用：`GET /api/health`、`POST /api/analyze`、指标口径 CRUD、`GET /api/runs` 和 `GET /api/memories`。

验证：已通过 `npm run backend:test`，73 个测试通过；已通过 `npm run frontend:build`；已通过 `npm run test:e2e`。

风险/后续：示例默认后端地址为 `http://localhost:8000`。后续如果改端口、引入鉴权、统一 API client 或修改 smoke 脚本，需要同步更新本文档。
