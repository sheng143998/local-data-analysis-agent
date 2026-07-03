# 前后端接口映射文档

本文档说明当前前端实际调用的 API、TypeScript 类型与后端接口契约之间的映射关系。它是 [V1 接口文档](api.md) 的补充，重点服务前端联调、字段变更和接口回归检查。错误码、权限边界和上线前鉴权建议见 [接口错误码与权限边界文档](api_error_auth.md)。

## 当前调用边界

前端只通过 `frontend/src/api/` 调用后端接口。

当前已存在的前端 API client：

| 文件 | 作用 | 后端接口 |
| --- | --- | --- |
| `frontend/src/api/analysisClient.ts` | 数据问答 | `POST /api/analyze` |
| `frontend/src/api/metricClient.ts` | 指标口径 CRUD | `GET/POST/PUT/DELETE /api/metrics` |

当前没有统一的 `frontend/src/api/client.ts`。两个 client 文件都各自读取：

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
```

后续如果要统一错误处理、鉴权 header、请求超时或 base URL，建议先抽出统一 client，再让 `analysisClient.ts` 和 `metricClient.ts` 复用。

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
  rows: AnalysisRow[];
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
| `trace` | 否 | 后端已返回，当前前端普通页面未声明和展示。 |
| `steps` | 否 | 后端已返回，当前前端普通页面未声明和展示。 |

注意：

- `trace` 和 `steps` 属于简化执行追踪信息，不是原始工具 payload。
- 普通用户界面不展示 SQL Memory 候选分数、prompt、模型原始输出或数据库连接状态。
- 如果后续需要在前端展示 Agent 执行步骤，应先扩展 `frontend/src/types/analysis.ts`，再调整页面组件。

### `rows` 当前结构

当前前端 `AnalysisRow` 结构为：

```ts
export type AnalysisRow = {
  date: string;
  amount: number;
  orders: number;
  avg: number;
  refundRate: string;
};
```

这适配当前 V1 的销售、订单、退款率等分析切片。后续如果 `/api/analyze` 支持任意表格列，建议把 `rows` 调整为更通用的结构，例如 `Record<string, string | number | null>[]`，并同步更新 `docs/api.md`。

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

- 前端当前只根据 `response.ok` 抛出中文通用错误，例如“创建指标失败”。
- 前端暂未读取后端 `detail` 字段。
- 后续如果要展示更精确错误，需要在 client 层解析 FastAPI 错误响应。

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

- 前端 API client 尚未统一封装，后续鉴权、超时、错误解析可能出现重复实现。
- 前端 `AnalysisResponse` 没有声明后端返回的 `trace` 和 `steps`，如果页面要展示执行步骤，需要补类型。
- `/api/analyze` 的 `rows` 类型还不是通用表格结构，后续扩展任意 SQL 结果时要更新前后端类型和文档。
