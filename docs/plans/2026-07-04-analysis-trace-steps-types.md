# 数据问答 Trace / Steps 前端类型契约计划

## Goal

本模块补齐前端 `AnalysisResponse` 与后端 `trace`、`steps` 的类型契约，让前端 API 类型完整覆盖当前 `/api/analyze` 响应。普通用户页面仍不展示 SQL Memory 候选分数、prompt、模型原始输出、数据库连接状态或工具 payload。

## Current task

当前正在做：验证已通过，准备提交并推送。

## Scope

包含：

- `frontend/src/types/analysis.ts` 增加 `AnalysisTrace` 和 `AgentStep` 类型。
- `AnalysisResponse` 声明后端已返回的 `trace` 和 `steps` 字段。
- 普通聊天页面继续不渲染内部追踪细节。
- 将聊天页头部“本地 PostgreSQL / 只读执行”改为更业务化的“只读安全分析”，避免普通用户看到数据库状态感文案。
- 更新接口映射、README、handoff、计划和模块完成说明。

不包含：

- 不新增开发者调试页面。
- 不调用 `/api/runs` 或 `/api/memories`。
- 不展示 SQL Memory 分数、prompt、模型原始输出、数据库连接状态或工具 payload。
- 不新增固定 SQL 模板。

## Module boundary

上游输入：

- 后端 `AnalyzeResponse.trace`。
- 后端 `AnalyzeResponse.steps`。

下游输出：

- 前端 `AnalysisResponse` 类型完整声明这些字段。
- 普通聊天页只使用 `summary`、`sql`、`rows` 等业务结果字段。

预计触达文件：

- `frontend/src/types/analysis.ts`
- `frontend/src/pages/ChatPage.tsx`
- `docs/api_frontend_mapping.md`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-analysis-trace-steps-types.md`

## Business logic

业务用户只需要看到分析结论、SQL、结果表和可信来源，不需要理解内部节点、模型调用或数据库状态。前端类型补齐是为了接口契约完整和后续开发者视图预留，不改变普通用户页面的信息边界。

## Data contract

新增前端类型：

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

`AnalysisResponse` 新增：

- `trace: AnalysisTrace`
- `steps: AgentStep[]`

## Implementation steps

- [x] 读取 handoff、接口映射和当前前端类型。
- [x] 补齐前端类型和普通用户文案。
- [x] 更新文档和模块说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `npm run frontend:build`
- `npm run backend:test`
- `npm run test:e2e`

本模块不修改后端语义和 SQL 生成路径，暂不强制运行 `npm run eval:standard`。

## Risks and open questions

- `trace` 和 `steps` 虽已进入类型，但普通用户页面仍不展示；后续如做开发者视图，需要明确权限边界。
- 如果后端以后扩展 `steps.status` 取值，需要同步更新 TypeScript union。
