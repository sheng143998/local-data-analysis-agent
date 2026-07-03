# 接口文档索引与阅读顺序模块完成说明

模块：接口文档索引与阅读顺序

当前状态：中文接口文档索引已补齐，README 和各接口文档入口已更新，验证已通过，准备随本次提交推送完成。

业务逻辑：本模块不修改任何 API 实现、前端 API client、测试脚本或数据库结构，只为当前接口文档体系增加统一入口。文档按第一次了解 API、前端联调、后端改接口、提交前验证、上线前审查等场景给出阅读顺序，并说明每份接口文档的职责和何时更新。

关键代码：本模块只涉及文档：

- `docs/api_index.md`：新增接口文档索引与阅读顺序。
- `README.md`：增加接口文档索引入口。
- `docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_error_auth.md`、`docs/api_change_process.md`、`docs/api_smoke_examples.md`：互链索引文档。
- `docs/plans/2026-07-03-api-doc-index.md`：记录本轮文档任务计划和边界。

数据契约：没有新增或修改 API 字段。文档只组织现有接口文档，覆盖当前 `GET /api/health`、`POST /api/analyze`、指标 CRUD、运行记录和 SQL Memory 调试接口的文档入口。

验证：已通过 `npm run backend:test`，73 个测试通过；已通过 `npm run frontend:build`；已通过 `npm run test:e2e`。

风险/后续：如果后续新增 OpenAPI 自动文档、开发者调试页接口文档或鉴权接口文档，需要同步更新索引。
