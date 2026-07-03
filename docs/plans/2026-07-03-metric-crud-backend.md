# 指标口径后端 CRUD 与迁移计划

Goal: 将指标口径从前端本地 state 升级为后端 API 管理的业务配置资产，并补充 PostgreSQL metadata migration。

当前正在做：模块已完成，前端构建、后端测试和 smoke 均已通过。

Scope:
- 包含：`metric_definitions` migration、Pydantic schema、FastAPI routes、service/repository、API tests、前端 metric API client、前端页面接入 React Query。
- 不包含：真实 PostgreSQL repository、embedding 写入、权限系统、审计日志。

Module boundary:
- Upstream inputs: 前端指标 CRUD 操作、后端 mock repository、metric migration。
- Downstream outputs: 指标列表、详情、新增、编辑、删除结果。
- Likely touched files: `backend/app/api`, `backend/app/schemas`, `backend/app/services`, `backend/app/db`, `backend/tests`, `frontend/src/api`, `frontend/src/types`, `frontend/src/components/metrics`。

Business logic:
- 业务分析人员可以维护统一指标口径。
- 新增/编辑/删除指标通过后端 API 完成。
- 数据问答后续可读取这些指标定义作为 SQL 生成约束。

Data contract:
- `GET /api/metrics`
- `GET /api/metrics/{metric_id}`
- `POST /api/metrics`
- `PUT /api/metrics/{metric_id}`
- `DELETE /api/metrics/{metric_id}`
- Metric fields: `id`, `metric_name`, `display_name`, `description`, `formula`, `required_tables`, `required_fields`, `default_filters`, `example_question`, `owner`, `status`, `created_at`, `updated_at`

Implementation steps:
- [x] 创建模块计划
- [x] 添加 PostgreSQL metadata migration
- [x] 添加后端 metric schema/repository/service/routes
- [x] 添加 API tests
- [x] 添加前端 metric 类型和 API client
- [x] 改造前端指标页调用 API
- [x] 运行前端构建、后端测试、smoke
- [x] commit 并 push

Validation plan:
- `npm run frontend:build`
- `npm run backend:test`
- `npm run test:e2e`

Risks and open questions:
- 当前先用内存 repository，后续 M1 完整数据库连接后替换为 PostgreSQL repository。
- 删除指标当前为硬删除；真实业务中可能需要软删除或状态停用。
