# 模块：数据问答 Trace / Steps 前端类型契约

当前状态：代码开发完成，验证已通过，随本次提交完成 commit 和 push，提交信息为 `补齐分析追踪前端类型并通过验证`。

业务逻辑：

本模块补齐前端对 `/api/analyze` 响应的类型声明。后端已经返回 `trace` 和 `steps`，前端现在也显式声明这些字段，后续开发者视图或受控分析过程摘要可以复用同一契约。普通用户聊天页仍不展示 SQL Memory 分数、prompt、模型原始输出、数据库连接状态或工具 payload。

关键代码：

- `frontend/src/types/analysis.ts`：新增 `AnalysisTrace`、`AgentStep`，并在 `AnalysisResponse` 中声明 `trace` 和 `steps`。
- `frontend/src/pages/ChatPage.tsx`：将顶部状态文案从“本地 PostgreSQL / 只读执行”调整为“只读安全分析”，避免普通用户界面出现数据库状态感文案。
- `docs/api_frontend_mapping.md`：同步前后端字段映射，说明 `trace` 和 `steps` 已有类型但普通用户页面不展示。

数据契约：

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

验证：

- `npm run frontend:build`：已通过。
- `npm run backend:test`：73 passed，1 个 `StarletteDeprecationWarning`，不影响本模块。
- `npm run test:e2e`：已通过，question -> FastAPI -> AgentService -> Guard -> Executor -> result。

风险/后续：

- `trace` 和 `steps` 已进入前端类型，但不等于普通用户页面应该展示内部追踪。后续如展示，应放在开发者视图或受控摘要中。
- 如果后端扩展 `AgentStep.status` 枚举，需要同步 TypeScript union。
