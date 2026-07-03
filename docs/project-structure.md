# 本地数据分析 Agent 项目结构

```text
.
├─ frontend/                  # React + Vite + TypeScript 前端
│  ├─ src/api/                # 前端集中 API client
│  ├─ src/types/              # 前端 API 类型
│  ├─ src/components/         # 复用 UI 组件
│  └─ src/pages/              # 页面路由
├─ backend/                   # FastAPI 后端
│  ├─ app/api/                # API 路由，保持薄层
│  ├─ app/services/           # 业务编排服务
│  ├─ app/agents/             # Agent/LangGraph 编排边界
│  ├─ app/tools/              # SQL 生成、校验、执行等工具边界
│  ├─ app/db/                 # PostgreSQL/pgvector 连接、仓储、迁移
│  ├─ app/schemas/            # Pydantic API 契约
│  └─ tests/                  # 后端 smoke 与 API 测试
├─ docs/plans/                # 模块开发计划
├─ package.json               # 项目级脚本入口
└─ *.md                       # 业务规划与说明文档
```

## 当前最小闭环

1. 用户在 `frontend` 聊天页输入自然语言问题。
2. 前端通过 `frontend/src/api/analysisClient.ts` 调用 `POST /api/analyze`。
3. FastAPI 路由进入 `AgentService`。
4. `AgentService` 调用 mock Agent graph。
5. graph 返回自然语言结论、SQL、结果表、来源与 trace。
6. 前端以聊天消息方式展示结果。

## 当前命令

```bash
npm run frontend:dev
npm run frontend:build
npm run backend:dev
npm run backend:test
npm run test:e2e
```

当前后端仍为 mock 数据闭环，不连接真实 PostgreSQL，不调用真实模型。
