# 本地数据分析 Agent

本项目是一个面向业务分析人员的本地化 AI 数据分析系统。用户可以像聊天一样提出业务问题，系统后端负责召回指标口径和表结构、生成或复用 SQL、通过 SQL Validator / SQL Guard、执行只读 PostgreSQL 查询，并返回自然语言结论、最终 SQL、结果表和数据来源。

普通用户界面聚焦可信分析结果；模型、数据库连接状态、SQL Memory 评分、工具调用 payload 和评估报告等调试信息默认不展示给业务用户。

## 当前能力

- 聊天式数据问答：`POST /api/analyze` 已接入真实 PostgreSQL 查询链路。
- 指标口径 CRUD：`GET/POST/PUT/DELETE /api/metrics` 已持久化到 `metric_definitions`。
- Schema + Metric Retriever：从 `schema_metadata` 和 `metric_definitions` 召回分析上下文。
- SQL 安全链路：SQL Validator + SQL Guard 拦截写操作、多语句、非白名单表和 `SELECT *`。
- 只读 SQL Executor：仅执行 Guard 放行后的 SELECT，并返回标准化 JSON 行数据。
- Query Run Logging：每次 analyze 会写入 `query_runs`，关键工具调用写入 `tool_calls`。
- SQL Memory：成功查询会写入 `sql_memories`，高置信历史问题可走 `fast_path` 复用已验证 SQL。
- 参数化模板：可解析“最近 7 天 / 30 天 / 90 天”等时间范围，并渲染销售趋势 SQL。
- SQL Rewriter / Generator 最小切片：可识别“最近 90 天每月订单数是多少？”这类按月订单数问题，生成或改写可执行 SQL。
- 商品/品类排行切片：可识别“销售额最高的前 10 个商品是什么？”和“哪个商品品类销售额最高？”，执行真实商品/品类销售额排行查询。
- 开发者调试 API：`GET /api/runs`、`GET /api/runs/{run_id}` 可查看运行记录和工具调用摘要。
- SQL Memory 调试 API：`GET /api/memories`、`GET /api/memories/{memory_id}` 可查看历史成功 SQL。

## 项目结构

```text
frontend/   React + Vite + TypeScript 前端
backend/    FastAPI 后端、Agent 编排、工具函数、PostgreSQL 访问
docs/       计划文档、模块完成说明、handoff、数据库说明
```

## 本地环境

后端依赖 PostgreSQL，本机当前使用：

```text
host: 127.0.0.1
port: 5432
database: local_data_agent
user: postgres
schema: public
```

本地真实密码只写在 `backend/.env`，不要提交到 Git。示例：

```env
DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5432/local_data_agent
```

## 常用命令

```bash
npm run backend:test
npm run test:e2e
npm run frontend:build
npm run backend:dev
npm run frontend:dev
```

## API 入口

- `GET /api/health`：服务健康检查。
- `POST /api/analyze`：聊天式数据问答。
- `GET /api/metrics`：指标口径列表。
- `POST /api/metrics`：创建指标口径。
- `PUT /api/metrics/{metric_id}`：更新指标口径。
- `DELETE /api/metrics/{metric_id}`：删除指标口径。
- `GET /api/runs`：开发者查看最近运行记录。
- `GET /api/runs/{run_id}`：开发者查看单次运行及工具调用。
- `GET /api/memories`：开发者查看 SQL Memory 列表。
- `GET /api/memories/{memory_id}`：开发者查看单条 SQL Memory。

## SQL Memory 当前说明

当前 SQL Memory 已支持最小参数化复用：

- 高置信历史问题会走 `fast_path`。
- 中置信历史问题会进入 `rewrite_path`，当前先用确定性 Rewriter 支持按月粒度和订单数问题。
- 时间范围、Top N、分析粒度和分析指标会从用户问题中解析为参数。
- 成功查询会把 `parameters`（含 `days`、`granularity`、`metric`）、最终 SQL、结果列和行数写入 `sql_memories`。
- 普通用户不默认看到 SQL Memory 候选分数；开发者通过 `/api/memories` 和 `/api/runs` 查看。

## 当前验证

最近一次模块验证通过：

```bash
npm run backend:test
npm run test:e2e
npm run frontend:build
```

## 开发约定

- 每次继续开发前先读取 `docs/handoff/current.md`。
- 每个模块先写 `docs/plans/YYYY-MM-DD-module-name.md`。
- 模块完成后写 `docs/modules/YYYY-MM-DD-module-name.md`。
- 通过相关测试后再提交并推送到 GitHub。
- 普通用户前端不默认展示模型、数据库连接、SQL 记忆评分、工具调用原始日志和评估报告。
