# 模块：统一前端 API Client 与错误解析

当前状态：代码开发完成，验证已通过，随本次提交完成 commit 和 push，提交信息为 `统一前端APIClient并通过验证`。

业务逻辑：

本模块让数据问答和指标口径 CRUD 统一通过前端 API Client 调用后端。用户发起分析、创建指标、编辑指标、删除指标时，如果后端返回 FastAPI `detail`，前端会尽量展示中文业务错误；如果是服务端异常或网络异常，则展示安全的兜底提示，不暴露模型状态、数据库连接状态、SQL Memory 分数、prompt 或调试 payload。

关键代码：

- `frontend/src/api/client.ts`：新增 `apiRequest<T>()` 和 `ApiError`，集中处理 base URL、JSON 请求体、响应解析、FastAPI `detail`、网络异常和常见状态码。
- `frontend/src/api/analysisClient.ts`：`analyzeQuestion()` 改为复用 `apiRequest<AnalysisResponse>()`。
- `frontend/src/api/metricClient.ts`：`listMetrics()`、`createMetric()`、`updateMetric()`、`deleteMetric()` 改为复用统一 client。

调用链路：

页面组件 -> `analysisClient.ts` / `metricClient.ts` -> `apiRequest<T>()` -> FastAPI `/api/...` -> typed JSON 或 `ApiError.message`。

数据契约：

- 成功响应类型不变，仍使用现有 `AnalysisResponse`、`MetricDefinition`、`MetricPayload`。
- 失败时统一抛出 `ApiError`：
  - `message`：中文用户可读错误。
  - `status`：HTTP 状态码，网络异常为 `0`。
  - `detail`：安全摘要，可供后续开发者 UI 或日志使用。

验证：

- `npm run frontend:build`：已通过。
- `npm run backend:test`：73 passed，1 个 `StarletteDeprecationWarning`，不影响本模块。
- `npm run test:e2e`：已通过，question -> FastAPI -> AgentService -> Guard -> Executor -> result。

风险/后续：

- 尚未实现请求超时、取消请求、自动重试和鉴权 header。
- `AnalysisResponse.trace` 与 `steps` 仍未进入前端类型；本模块按普通用户页面不展示内部追踪的原则保持不变。
- 本模块不新增固定 SQL 模板；后续应继续推进 schema/metric/memory/model-ready 的通用能力。
