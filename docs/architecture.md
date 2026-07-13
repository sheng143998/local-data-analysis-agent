# Agent 架构说明

## 产品边界

本项目是面向业务分析人员的本地化数据分析 Agent。普通用户通过聊天式页面提问，系统返回业务结论、SQL、结果表、来源和可信说明。模型状态、数据库连接状态、prompt、SQL Memory 分数、工具 payload 和评估报告不进入普通用户主界面。

当前实现已经从早期的 mock 闭环升级为真实 PostgreSQL + LangGraph 主链路。模型只能产生候选意图或 SQL，不能直接执行 SQL；最终执行必须经过 QuerySpec/Query Plan 对齐、SQL Inspector、SQL Validator、SQL Guard 和只读 Executor。

## 代码结构

```text
frontend/   React + Vite + TypeScript 普通用户前端
backend/    FastAPI API、Agent 编排、工具函数、数据库访问
eval/       标准回归与 authenticated 真值评估数据集、脚本和报告
docs/       计划、模块记录、handoff 和核心说明文档
```

核心后端边界：

- `backend/app/api/`：FastAPI 路由，保持薄层。
- `backend/app/services/`：业务服务，例如 `AgentService`、`MetricService`、`RunService`。
- `backend/app/agents/`：Agent 编排，主入口是 `analysis_graph.py`。
- `backend/app/tools/`：检索、Query Plan、SQL Memory、SQL 生成、Inspector、Guard、Executor 和 Presenter。
- `backend/app/db/`：PostgreSQL 连接、迁移和 repository。
- `backend/app/core/`：配置、ModelAdapter、EmbeddingAdapter 和 Model Routing。
- `eval/`：标准 20 题快速回归、50 题 authenticated 真值评测和失败归因脚本。

## 主链路

```text
React ChatPage
-> POST /api/analyze
-> AgentService
-> Semantic Resolver + Clarification Policy
-> Query Plan + Context Pack
-> schema/metric/relationship retrieval + rerank
-> Trusted SQL Memory retrieval and verification
-> model SQL generation/rewrite (role-based routing)
-> SQL Intent Validator + Inspector/Repair
-> SQL Guard
-> read-only PostgreSQL Executor
-> Result Contract + Presenter
-> QueryRunLogger
-> verified SQL Memory update
```

如果用户问题缺少必要业务对象或存在已注册契约冲突，Clarification Policy 返回结构化追问；未知但明确的概念不会因为未命中词表而自动追问。信息足够时直接进入 Query Plan 和 SQL 生成链路。

## 已交付能力

- **Semantic Contract / Resolver**：版本化保存指标、实体、维度、来源字段、业务定义和结果形态；Resolver 只做结构化语义绑定，不生成 SQL。
- **Clarification Policy**：只依据缺失槽位或契约冲突决定是否追问，并保留自然语言模型生成追问的入口。
- **Trusted SQL Memory**：SQL Memory 有 candidate、executed、reviewed、verified 等生命周期；只有 verified 候选可尝试 fast path，复用前仍需重新校验。
- **Query Plan / Context Pack**：把实体、度量、维度、过滤器、时间半开区间、排序、LIMIT 和预期结果形态固化为结构化计划，再裁剪模型上下文；计划本身不执行 SQL。
- **Inspector / Repair**：在 Guard 前按 Query Plan 检查实体表、度量、维度、时间边界、排行排序和 Top N，并按类别输出可复制 Repair Rule。
- **Result Contract / Presenter**：使用真实返回列角色、结果行、范围和告警生成通用摘要，区分空结果、零值和不可计算结果。
- **Model Routing / Observability**：意图、SQL 生成和 SQL 修复使用显式任务角色路由，run trace 只记录 provider/model/latency 摘要，不记录密钥或完整 prompt。
- **SQL 安全边界**：模型和 Memory 的 SQL 都必须经过 Validator、Inspector、Guard 和只读 Executor；写操作、多语句、非白名单表、未知字段、`SELECT *` 和超限结果会被拦截。

## 质量状态

可信 50-case 基线为 `eval/reports/post_upgrade_full_eval.json`：执行成功 `31/50`、严格成功 `13/50`、答案匹配 `14/48`。该结果证明链路、鉴权、run trace 和安全边界可追踪，但本地 `qwen2.5-coder:3b` 仍会产生空 SQL、错误 JOIN 或错误聚合粒度，后续应使用稳定模型配置继续做失败归因和模型对照。

## 关键原则

- 普通用户界面只展示可信分析结果。
- 开发者调试信息进入 `/api/runs`、`/api/memories`、日志和评估报告。
- LLM 不能直接执行 SQL。
- 任何生成或复用的 SQL 都必须通过 Query Plan/Inspector、Validator、Guard 和只读 Executor。
- 换库或表结构变化后先运行 schema metadata 和 embedding 刷新脚本。
- 评估结果必须区分 authenticated 50-case 可信基线和标准 20-case 快速工件，不能互相替代。
