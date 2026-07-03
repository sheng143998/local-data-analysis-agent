# V1 架构说明

## 产品边界

本项目是面向业务分析人员的本地化数据分析 Agent。普通用户通过聊天式页面提问，系统返回业务结论、SQL、表格、来源和可信说明。模型状态、数据库连接状态、prompt、SQL Memory 分数、工具 payload 和评估报告不进入普通用户主界面。

## 代码结构

```text
frontend/   React + Vite + TypeScript 普通用户前端
backend/    FastAPI API、Agent 编排、工具函数、数据库访问
eval/       标准问题评估数据集、脚本和报告
docs/       计划、模块记录、handoff 和核心说明文档
```

核心后端边界：

- `backend/app/api/`：FastAPI 路由，保持薄层。
- `backend/app/services/`：业务服务，例如 `AgentService`、`MetricService`、`RunService`。
- `backend/app/agents/`：Agent 编排，目前主入口是 `analysis_graph.py`。
- `backend/app/tools/`：确定性工具，包括 schema/metric 检索、SQL Memory、SQL 生成、SQL Guard、Executor、Presenter。
- `backend/app/db/`：PostgreSQL 连接、迁移和 repository。
- `backend/app/core/`：配置和统一 `ModelAdapter`。

## 主链路

```text
React ChatPage
-> POST /api/analyze
-> AgentService
-> analysis_graph.run_analysis_graph
-> build_retrieval_context
-> retrieve_sql_memory
-> plan_sql_reuse
-> select_generated_sql
-> guard_sql
-> execute_guarded_sql
-> present_sales_trend_result
-> QueryRunLogger
-> upsert_successful_sql_memory
```

## 当前实现事实

- `/api/analyze` 已执行真实 PostgreSQL 查询。
- SQL 必经 Guard 和只读 Executor。
- SQL Memory 已支持检索、复用、写入和 fast_path 关键表约束。
- ModelAdapter 和 model-backed SQL Generator 已有基础层，prompt payload 由结构化函数生成并有测试覆盖。
- `MODEL_SQL_GENERATOR_ENABLED=false` 默认关闭真实模型 SQL 生成，开启后仅 `cold_path` 尝试模型生成，失败会回退。
- 标准问题评估已可运行，并区分链路成功和严格断言成功。

## 关键原则

- 普通用户界面只展示可信分析结果。
- 开发者调试信息进入 `/api/runs`、`/api/memories`、日志和评估报告。
- LLM 不能直接执行 SQL。
- 模型生成 SQL 仍必须经过 Validator、Guard 和只读 Executor；编造字段、`SELECT *`、非白名单表和写操作会在执行前被拦截。
- 换库或表结构变化后先运行 schema metadata 同步脚本。
