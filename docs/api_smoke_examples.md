# 接口联调与 Smoke 示例文档

本文档说明如何在本地用命令行快速联调 V1 API，以及 `npm run test:e2e` 当前验证了哪些链路。它是 [V1 接口文档](api.md)、[前后端接口映射文档](api_frontend_mapping.md)、[接口错误码与权限边界文档](api_error_auth.md) 和 [接口变更流程与版本维护文档](api_change_process.md) 的补充。

## 本地启动

后端开发服务：

```bash
npm run backend:dev
```

默认地址：

```text
http://localhost:8000
```

前端开发服务：

```bash
npm run frontend:dev
```

前端 API base URL 默认来自：

```text
VITE_API_BASE_URL
```

如果未配置，前端当前默认调用：

```text
http://localhost:8000
```

## 自动 Smoke

当前 E2E smoke 命令：

```bash
npm run test:e2e
```

实际执行脚本：

```text
backend/tests/smoke_api.py
```

当前检查点：

- `GET /api/health` 返回 `200`。
- `POST /api/analyze` 返回 `200`。
- `/api/analyze` 响应里的 `source.security` 包含 `SQL Guard`。
- `/api/analyze` 响应里的 `rows` 非空。

通过输出：

```text
backend smoke passed: question -> FastAPI -> AgentService -> Guard -> Executor -> result
```

注意：

- `npm run test:e2e` 是最小链路 smoke，不等于完整语义评估。
- 如果要检查 20 个标准问题，应运行 `npm run eval:standard`。

## PowerShell 调用示例

### 健康检查

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/api/health"
```

预期结果：

```json
{
  "ok": true,
  "service": "local-data-analysis-agent",
  "version": "0.1.0"
}
```

### 数据问答

```powershell
$body = @{
  question = "最近 30 天销售额按天变化如何？"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method POST `
  -Uri "http://localhost:8000/api/analyze" `
  -ContentType "application/json" `
  -Body $body
```

重点检查：

- `summary` 是中文分析结论。
- `sql` 非空。
- `source.security` 包含 SQL Guard 或只读说明。
- `rows` 有结果。
- `path` 是 `fast_path`、`rewrite_path` 或 `cold_path`。

### 指标口径列表

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/api/metrics"
```

重点检查：

- 返回数组。
- 每条记录包含 `metric_name`、`display_name`、`formula`、`status`。

### 创建测试指标

```powershell
$metric = @{
  metric_name = "test_metric_for_doc"
  display_name = "测试指标"
  description = "接口文档联调用测试指标"
  formula = "COUNT(*)"
  required_tables = @("orders")
  required_fields = @("orders.id")
  default_filters = @{}
  example_question = "测试指标是多少？"
  owner = "接口联调"
  status = "draft"
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Method POST `
  -Uri "http://localhost:8000/api/metrics" `
  -ContentType "application/json" `
  -Body $metric
```

注意：

- 手工创建测试指标后，建议记录返回的 `id` 并在联调结束时删除。
- 不要在文档或提交中写入真实业务密钥、数据库密码或私有连接串。

### 删除测试指标

```powershell
$metricId = "<替换为创建接口返回的 id>"

Invoke-RestMethod `
  -Method DELETE `
  -Uri "http://localhost:8000/api/metrics/$metricId"
```

预期结果：

```json
{
  "deleted": true
}
```

### 查看运行记录

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/api/runs?limit=5"
```

说明：

- 这是开发者调试接口。
- 普通用户主导航不展示该接口。
- 返回内容可能包含用户问题、SQL、执行状态和错误摘要。

### 查看 SQL Memory

```powershell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/api/memories?limit=5"
```

说明：

- 这是开发者调试接口。
- 普通用户主导航不展示该接口。
- 返回内容可能包含历史成功 SQL 和参数。

## curl 调用示例

### 健康检查

```bash
curl http://localhost:8000/api/health
```

### 数据问答

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"最近 30 天销售额按天变化如何？\"}"
```

### 指标列表

```bash
curl http://localhost:8000/api/metrics
```

## 验证命令分层

| 命令 | 用途 | 适用场景 |
| --- | --- | --- |
| `npm run backend:test` | 后端单元/API 测试。 | 后端接口、schema、工具、repository 变更后。 |
| `npm run frontend:build` | 前端类型检查和构建。 | 前端类型、API client、页面展示变更后。 |
| `npm run test:e2e` | 最小 API 链路 smoke。 | 每次模块提交前。 |
| `npm run eval:standard` | 20 个标准问题评估。 | `/api/analyze` 语义、SQL 生成、SQL Memory 或评估相关变更后。 |

## 常见问题

### 后端没有启动

现象：

- PowerShell 或 curl 连接失败。
- 前端提示接口调用失败。

处理：

```bash
npm run backend:dev
```

### 数据库不可用

现象：

- `/api/analyze` 或 `/api/metrics` 返回服务端错误。
- 后端日志出现数据库连接错误。

处理：

- 确认 PostgreSQL 正在运行。
- 确认 `backend/.env` 中 `DATABASE_URL` 正确。
- 不要把真实密码写入 README 或文档示例。

### 指标删除后再次查询返回 404

这是正常行为。当前后端会返回：

```json
{
  "detail": "指标不存在"
}
```

### `/api/runs` 或 `/api/memories` 有数据

这是正常行为。它们是开发者调试接口，用于查看 Agent 运行记录和 SQL Memory，不属于普通用户主页面能力。

## 文档维护要求

如果接口路径、字段、错误码或权限边界变化，需要同步更新：

- `docs/api.md`
- `docs/api_frontend_mapping.md`
- `docs/api_error_auth.md`
- `docs/api_change_process.md`
- 本文档
- `README.md`
- `docs/handoff/current.md`
