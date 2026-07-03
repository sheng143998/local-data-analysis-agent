# 模块完成说明：指标口径 PostgreSQL Repository

模块：指标口径 PostgreSQL Repository

当前状态：已完成，`/api/metrics` 已从内存仓储切换为 PostgreSQL `metric_definitions` 表，已通过测试，准备提交推送。

业务逻辑：
- 指标口径是业务配置资产，需要持久化保存。
- 前端通过 `/api/metrics` 新增、编辑、删除指标后，数据写入 PostgreSQL。
- 后端重启后，指标数据仍保留。

关键代码：
- `backend/app/db/repositories/metric_repository.py`：PostgreSQL 指标仓储。
- `backend/app/services/metric_service.py`：指标业务服务，保持 API 层薄。
- `backend/app/api/metrics.py`：指标 CRUD API。
- `backend/tests/test_metrics.py`：覆盖列表、新增、更新、详情、删除。

数据契约：
- API 不变：
  - `GET /api/metrics`
  - `GET /api/metrics/{metric_id}`
  - `POST /api/metrics`
  - `PUT /api/metrics/{metric_id}`
  - `DELETE /api/metrics/{metric_id}`
- Persistence: `metric_definitions`

验证：
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

风险/后续：
- 当前测试直接使用本地数据库，后续需要独立测试库或事务回滚 fixture。
- 指标删除当前是硬删除，真实业务可能改为软删除或状态停用。
