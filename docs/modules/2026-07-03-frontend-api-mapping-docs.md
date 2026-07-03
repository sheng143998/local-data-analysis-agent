# 前后端接口映射文档模块完成说明

模块：前后端接口映射文档

当前状态：中文映射文档已补齐，README 和 `docs/api.md` 入口已更新，验证已通过，准备随本次提交推送完成。

业务逻辑：本模块不修改前端代码、后端接口、数据库结构或 Agent 行为，只记录当前前端 API client 如何调用后端接口、TypeScript 类型覆盖了哪些响应字段、哪些后端调试字段暂未进入普通用户页面。文档明确开发者调试接口 `/api/runs` 和 `/api/memories` 当前没有普通前端入口。

关键代码：本模块只涉及文档：

- `docs/api_frontend_mapping.md`：新增前后端接口映射文档，覆盖页面到接口、client 函数到后端路由、类型字段映射和接口变更同步清单。
- `README.md`：在 V1 核心文档和 API 入口说明中加入映射文档链接。
- `docs/api.md`：加入映射文档链接。
- `docs/plans/2026-07-03-frontend-api-mapping-docs.md`：记录本轮文档任务计划和边界。

数据契约：没有新增或修改接口字段。文档记录当前真实映射：`analyzeQuestion(question)` 对应 `POST /api/analyze`，`listMetrics/createMetric/updateMetric/deleteMetric` 对应指标口径 CRUD。文档同时记录前端 `AnalysisResponse` 当前没有声明后端返回的 `trace` 和 `steps`。

验证：已通过 `npm run frontend:build`；已通过 `npm run backend:test`，73 个测试通过；已通过 `npm run test:e2e`。

风险/后续：前端目前没有统一 `client.ts`，两个 API client 各自维护 `API_BASE_URL`；后续如增加鉴权、统一错误解析或超时控制，需要同步更新前端 API client 和本文档。
