# 本地数据分析 Agent 项目结构

```text
.
├─ frontend/                  # React + Vite + TypeScript 用户前端
│  ├─ src/api/                # 前端集中 API client
│  ├─ src/types/              # 前端 API 类型
│  ├─ src/components/         # 复用 UI 组件
│  └─ src/pages/              # 页面路由
├─ backend/                   # FastAPI 后端
│  ├─ app/api/                # API 路由，保持薄层
│  ├─ app/services/           # 业务编排服务、会话和记忆服务
│  ├─ app/agents/             # Agent/LangGraph 编排边界
│  ├─ app/tools/              # 检索、Query Plan、SQL 生成、Inspector、Guard、执行和 Presenter
│  ├─ app/core/               # 配置、ModelAdapter、EmbeddingAdapter、Model Routing
│  ├─ app/db/                 # PostgreSQL/pgvector 连接、仓储、迁移
│  ├─ app/schemas/            # Pydantic API 和内部契约
│  └─ tests/                  # 后端 focused、API 和 smoke 测试
├─ eval/                      # 标准回归、50-case 真值评测、脚本和报告
├─ docs/plans/                # 开发前计划
├─ docs/modules/              # 完成模块记录和验证证据
├─ docs/handoff/              # 当前状态、风险和下一步
├─ package.json               # 项目级脚本入口
└─ *.md                       # 项目入口和业务规划说明
```

## 当前真实闭环

1. 用户在 `frontend` 聊天页输入自然语言问题。
2. 前端通过 `frontend/src/api/analysisClient.ts` 调用 `POST /api/analyze`。
3. FastAPI 路由进入 `AgentService`，由 LangGraph `StateGraph` 编排。
4. Semantic Resolver 和 Clarification Policy 判断是否缺少必要业务信息。
5. 信息足够时生成 Query Plan，召回并压缩 schema/指标/关系上下文。
6. SQL Memory 候选经过 trusted 状态和当前 Query Plan 校验；未通过时由角色路由的模型生成或改写 SQL。
7. SQL 经 Inspector/Repair、SQL Validator、SQL Guard 和只读 PostgreSQL Executor 执行。
8. Result Contract/Presenter 返回自然语言摘要、SQL、来源和通用结果表，写入安全运行摘要与 SQL Memory。

## 常用命令

```bash
npm run frontend:dev
npm run frontend:build
npm run backend:dev
npm run backend:test
npm run test:e2e
npm run eval:standard
npm run eval:database-baseline -- --start 0 --limit 10 --report eval/reports/database_batch_001.json
```

## 交付与安全边界

- 版本化计划、handoff 和模块记录是开发流程的一部分；每个通过验证的模块必须单独提交并推送。
- 任何模型生成或历史复用 SQL 都必须经过 Query Plan/Inspector、Validator、Guard 和只读 Executor。
- `backend/.env`、数据库密码、模型密钥、完整 prompt、原始 SQL 和用户数据不得提交。
- 当前可信质量基线为 `eval/reports/post_upgrade_full_eval.json`，执行 `31/50`、严格 `13/50`、答案 `14/48`；该结果用于后续对照，不代表质量达标。
