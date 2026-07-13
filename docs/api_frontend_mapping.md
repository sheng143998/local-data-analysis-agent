# 前后端接口映射文档

本文档说明当前前端实际调用的 API、TypeScript 类型与后端接口契约之间的映射关系。它是 [V1 接口文档](api.md) 的补充，重点服务前端联调、字段变更和接口回归检查。阅读顺序见 [接口文档索引与阅读顺序](api_index.md)，错误码、权限边界和上线前鉴权建议见 [接口错误码与权限边界文档](api_error_auth.md)，接口字段变更时按 [接口变更流程与版本维护文档](api_change_process.md) 同步，手工联调命令见 [接口联调与 Smoke 示例文档](api_smoke_examples.md)。

## 当前调用边界

前端只通过 `frontend/src/api/` 调用后端接口。

当前已存在的前端 API client：

| 文件 | 作用 | 后端接口 |
| --- | --- | --- |
| `frontend/src/api/client.ts` | 统一请求入口、base URL、JSON 解析和 FastAPI 错误解析 | 所有前端业务 client 复用 |
| `frontend/src/api/analysisClient.ts` | 数据问答 | `POST /api/analyze` |
| `frontend/src/api/authClient.ts` | 登录态 | `POST /api/auth/login`、`POST /api/auth/register`、`POST /api/auth/logout`、`GET /api/auth/me`；后端还提供自身 session 的查看与撤销 |
| `frontend/src/api/analysisClient.ts` | 会话恢复 | `GET /api/conversations` cursor 分页、`GET /api/conversations/{conversation_id}` 消息窗口分页 |
| `frontend/src/api/userMemoryClient.ts` | 长期偏好 | `GET/DELETE /api/user-memories` |
| `frontend/src/api/metricClient.ts` | 指标口径 CRUD | `GET/POST/PUT/DELETE /api/metrics` |

当前前端 API client 已统一读取：

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
```

`analysisClient.ts` 和 `metricClient.ts` 不再直接调用 `fetch`，而是复用 `apiRequest<T>()`。后续如果要增加鉴权 header、请求超时、统一重试或开发者接口隔离，优先在 `frontend/src/api/client.ts` 修改。

## 页面到接口映射

| 页面或组件 | 前端调用 | 后端接口 | 用途 |
| --- | --- | --- | --- |
| `frontend/src/pages/ChatPage.tsx` | `analyzeQuestion(question)` | `POST /api/analyze` | 用户输入业务问题后获取自然语言结论、SQL、表格和来源信息。 |
| `frontend/src/components/metrics/MetricDefinitionCards.tsx` | `listMetrics()` | `GET /api/metrics` | 加载指标口径列表。 |
| `frontend/src/components/metrics/MetricDefinitionCards.tsx` | `createMetric(payload)` | `POST /api/metrics` | 新增指标口径。 |
| `frontend/src/components/metrics/MetricDefinitionCards.tsx` | `updateMetric(id, payload)` | `PUT /api/metrics/{metric_id}` | 编辑指标口径。 |
| `frontend/src/components/metrics/MetricDefinitionCards.tsx` | `deleteMetric(id)` | `DELETE /api/metrics/{metric_id}` | 删除指标口径。 |

## 数据问答字段映射

### 前端调用

```ts
analyzeQuestion(question: string): Promise<AnalysisResponse>
```

请求：

```json
{
  "question": "最近 30 天销售额按天变化如何？"
}
```

后端接口：`POST /api/analyze`

### 前端类型

文件：`frontend/src/types/analysis.ts`

```ts
export type AnalysisResponse = {
  question: string;
  path: 'fast_path' | 'rewrite_path' | 'cold_path';
  summary: string;
  sql: string;
  metrics: AnalysisMetric[];
  rows: Record<string, string | number | boolean | null>[];
  source: {
    dataset: string;
    tables: string[];
    fields: string[];
    metricDefinition: string;
    range: string;
    returnedRows: number;
    queryTime: string;
    security: string;
  };
  trace: AnalysisTrace;
  steps: AgentStep[];
};
```

### 后端响应字段使用情况

| 后端字段 | 前端类型是否声明 | 当前前端用途 |
| --- | --- | --- |
| `question` | 是 | 用于保留用户问题上下文。 |
| `path` | 是 | 可用于区分 `fast_path`、`rewrite_path`、`cold_path`。 |
| `summary` | 是 | 聊天回答主体。 |
| `sql` | 是 | 展示最终 SQL。 |
| `metrics` | 是 | 展示指标摘要。 |
| `rows` | 是 | 展示结果表和图表数据。 |
| `source` | 是 | 展示数据来源、字段、口径、耗时和安全说明。 |
| `trace` | 是 | 前端类型已声明，普通用户页面不展示内部追踪细节。 |
| `steps` | 是 | 前端类型已声明，普通用户页面不展示内部执行步骤。 |

注意：

- `trace` 和 `steps` 属于简化执行追踪信息，不是原始工具 payload。
- 普通用户界面不展示 SQL Memory 候选分数、prompt、模型原始输出或数据库连接状态。
- 如果后续需要在前端展示 Agent 执行步骤，应优先建设开发者视图或受控的“分析过程摘要”，不要把原始工具 payload 放入普通用户页面。

### Trace 和 Steps 类型

文件：`frontend/src/types/analysis.ts`

```ts
export type AnalysisTrace = {
  toolCalls: number;
  modelCalls: number;
  memoryCandidates: number;
  totalTime: string;
};

export type AgentStep = {
  name: string;
  status: '已完成' | '运行中' | '已跳过';
  time: string;
};
```

说明：

- 类型契约覆盖后端响应，方便后续开发者调试视图复用。
- 普通用户聊天页当前不渲染 `trace` 和 `steps`。
- 聊天页头部已使用“只读安全分析”这类业务化文案，不展示数据库连接状态。

### `rows` 当前结构

当前前端 `AnalysisRow` 已改为通用结构：

```ts
export type AnalysisValue = string | number | boolean | null;
export type AnalysisRow = Record<string, AnalysisValue>;
```

后端 `rows` 字段直接来自 SQL Executor 的真实结果列，例如 `order_date`、`daily_sales`、`order_count`、`avg_order_value`、`city_label`、`success_rate`。`frontend/src/pages/ChatPage.tsx` 会根据返回行动态生成最多 6 列表头，并对常见列名做中文展示。

## 指标口径字段映射

### 前端类型

文件：`frontend/src/types/metric.ts`

```ts
export type MetricDefinition = {
  id: string;
  metric_name: string;
  display_name: string;
  description: string;
  formula: string;
  required_tables: string[];
  required_fields: string[];
  default_filters: Record<string, string>;
  example_question: string;
  owner: string;
  status: 'enabled' | 'draft' | 'disabled';
  created_at: string;
  updated_at: string;
};
```

前端创建和更新使用：

```ts
export type MetricPayload = Omit<MetricDefinition, 'id' | 'created_at' | 'updated_at'>;
```

### 字段映射

| 前端字段 | 后端字段 | 说明 |
| --- | --- | --- |
| `id` | `id` | UUID 字符串。创建时由后端生成。 |
| `metric_name` | `metric_name` | 机器可读指标名。 |
| `display_name` | `display_name` | 中文展示名。 |
| `description` | `description` | 指标说明。 |
| `formula` | `formula` | 指标公式或口径。 |
| `required_tables` | `required_tables` | 依赖表。 |
| `required_fields` | `required_fields` | 依赖字段。 |
| `default_filters` | `default_filters` | 默认过滤条件。 |
| `example_question` | `example_question` | 示例问题。 |
| `owner` | `owner` | 负责人。 |
| `status` | `status` | `enabled`、`draft` 或 `disabled`。 |
| `created_at` | `created_at` | 创建时间。 |
| `updated_at` | `updated_at` | 更新时间。 |

### 调用映射

| 前端函数 | 请求方法 | 后端路径 | 请求体 | 响应 |
| --- | --- | --- | --- | --- |
| `listMetrics()` | `GET` | `/api/metrics` | 无 | `MetricDefinition[]` |
| `createMetric(payload)` | `POST` | `/api/metrics` | `MetricPayload` | `MetricDefinition` |
| `updateMetric(id, payload)` | `PUT` | `/api/metrics/{id}` | `Partial<MetricPayload>` | `MetricDefinition` |
| `deleteMetric(id)` | `DELETE` | `/api/metrics/{id}` | 无 | `{ deleted: boolean }` |

错误处理现状：

- 前端通过 `frontend/src/api/client.ts` 统一解析 FastAPI `detail`。
- `detail` 为中文字符串时，普通业务错误会直接展示，例如“指标不存在”。
- `detail` 为 Pydantic 数组时，会收敛为“请求参数不完整或格式不正确”类中文提示。
- `500` 和网络异常不会把内部异常、数据库连接状态、模型状态或调试 payload 暴露给普通用户。

## 开发者调试接口前端状态

当前没有普通前端页面调用：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/memories`
- `GET /api/memories/{memory_id}`

这些接口属于开发者调试接口，用于查看运行记录、工具调用摘要和 SQL Memory。除非后续明确建设开发者调试页，否则不要把它们放入普通用户主导航。

## 接口变更同步清单

每次修改接口时，至少同步检查：

- `backend/app/api/*.py`
- `backend/app/schemas/*.py`
- `frontend/src/api/*.ts`
- `frontend/src/types/*.ts`
- `docs/api.md`
- `docs/api_frontend_mapping.md`
- `README.md`
- 相关测试和模块完成说明

## 当前风险

- 前端 API client 已统一封装，但尚未实现请求超时、取消请求和鉴权 header。
- 前端 `AnalysisResponse` 已声明后端返回的 `trace` 和 `steps`，普通用户页面仍不展示内部调试细节。
- `/api/analyze` 的 `rows` 已改为通用表格结构；后续风险转为自然语言总结仍主要面向 V1 已覆盖指标。
- `AuthProvider` 在应用启动时调用 `getCurrentUser()`；`ProtectedRoute` 在未登录时将 `/app/*` 跳转到 `/login`，并保留原始路径用于登录后恢复。
- `apiRequest()` 使用 `credentials: 'include'`，并从 CSRF Cookie 读取 token 后为非 `GET` 请求设置 `X-CSRF-Token`。
- `ChatPage` 保存分析响应返回的 `conversation_id`，后续提问复用该 ID；会话栏消费 `items/next_cursor`，消息区消费 `messages/has_more/next_before`，为后续虚拟列表和向上加载保留稳定契约。
- `ProfilePanel` 展示 active 长期偏好，并允许用户撤销偏好；偏好写入仍通过聊天中的明确“记住”指令完成。
