# 指标口径 PostgreSQL Repository 计划

Goal: 将指标 CRUD 从内存仓储替换为真实 PostgreSQL 仓储，并补齐 DataGrip 连接说明和模块完成文档。

当前正在做：模块已完成，PostgreSQL repository 已实现并通过验证，准备提交推送。

Scope:
- 包含：DataGrip 说明、PostgreSQL 数据基础模块完成文档、metric repository 切换为 PostgreSQL、测试更新、handoff 更新、commit/push。
- 不包含：前端新 UI、权限控制、指标 embedding 写入。

Module boundary:
- Upstream inputs: `/api/metrics` 请求、`metric_definitions` 表、`backend/.env`。
- Downstream outputs: 持久化指标 CRUD。
- Likely touched files: `backend/app/db/repositories/metric_repository.py`, `backend/app/services/metric_service.py`, `backend/tests`, `docs/`。

Business logic:
- 指标口径是业务配置资产，必须写入 PostgreSQL，不能停留在进程内存。
- 前端新增/编辑/删除指标后，后端重启也应保留。

Data contract:
- API 不变：`GET/POST/PUT/DELETE /api/metrics`
- Persistence: `metric_definitions`

Implementation steps:
- [x] 创建计划和补齐文档
- [x] 实现 PostgreSQL MetricRepository
- [x] 更新测试
- [x] 运行验证
- [x] 更新 handoff
- [x] commit 并 push

Validation plan:
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

Risks and open questions:
- 测试环境没有独立测试数据库，API 测试需要避免污染真实本地数据。
