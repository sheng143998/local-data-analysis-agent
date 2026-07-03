# 本地数据分析 Agent

本项目是一个面向业务分析人员的本地化 AI 数据分析系统。用户可以像聊天一样提出业务问题，系统后端负责召回指标口径和表结构、生成或复用 SQL、通过 SQL Validator / SQL Guard、执行只读 PostgreSQL 查询，并返回自然语言结论、最终 SQL、结果表和数据来源。

普通用户界面聚焦可信分析结果；模型、数据库连接状态、SQL Memory 评分、工具调用 payload 和评估报告等调试信息默认不展示给业务用户。

## 当前能力

- 聊天式数据问答：`POST /api/analyze` 已接入真实 PostgreSQL 查询链路。
- 指标口径 CRUD：`GET/POST/PUT/DELETE /api/metrics` 已持久化到 `metric_definitions`。
- Schema + Metric Retriever：从 `schema_metadata` 和 `metric_definitions` 召回分析上下文，已接入文本分数 + pgvector 语义候选的混合检索；向量不可用时自动退回文本检索。
- Schema Metadata 自动同步：可从当前 PostgreSQL `information_schema` 刷新 `schema_metadata`，支持换库、换表后的字段上下文更新。
- 统一 ModelAdapter 基础层：已提供 OpenAI-compatible chat completions 适配器、模型配置、超时、重试和结构化错误，后续 SQL Generator 必须通过该入口调用模型。
- Model-backed SQL Generator 基础工具：已能基于召回到的 schema/metric 构造受控 prompt、调用 ModelAdapter、解析模型 JSON SQL；当前尚未替换 `/api/analyze` 主链路。
- Model SQL Generator cold_path 接入：`/api/analyze` 已具备配置开关式模型 SQL 生成入口，默认关闭；开启后仅 `cold_path` 尝试模型生成，失败会回退到稳定生成路径，最终 SQL 仍必经 Guard 和只读 Executor。
- SQL 安全链路：SQL Validator + SQL Guard 拦截写操作、多语句、非白名单表和 `SELECT *`。
- 只读 SQL Executor：仅执行 Guard 放行后的 SELECT，并返回标准化 JSON 行数据。
- Query Run Logging：每次 analyze 会写入 `query_runs`，关键工具调用写入 `tool_calls`。
- SQL Memory：成功查询会写入 `sql_memories` 并同步 question/sql embedding；高置信历史问题可走 `fast_path` 复用已验证 SQL。
- 参数化模板：可解析“最近 7 天 / 30 天 / 90 天”等时间范围，并渲染销售趋势 SQL。
- SQL Rewriter / Generator 最小切片：可识别“最近 90 天每月订单数是多少？”这类按月订单数问题，生成或改写可执行 SQL。
- 商品/品类排行切片：可识别“销售额最高的前 10 个商品是什么？”和“哪个商品品类销售额最高？”，执行真实商品/品类销售额排行查询。
- 复杂指标切片：可识别“哪个商品品类退款率最高？”和“每个支付方式的成功率是多少？”，执行真实退款率与支付成功率查询。
- 毛利率切片：可识别“最近 30 天毛利率最高的商品品类是什么？”，基于商品明细销售额和商品成本表计算品类毛利率。
- 用户维度切片：可识别“最近 90 天复购率是多少？”和“每个城市的客单价是多少？”，执行真实用户复购率与城市客单价查询。
- 前端统一 API Client：数据问答和指标 CRUD 已统一通过 `frontend/src/api/client.ts` 调用后端，支持 FastAPI `detail` 解析和中文错误提示。
- 通用结果表：`/api/analyze.rows` 已改为 SQL 执行结果的通用表格结构，前端聊天页会动态生成表头，减少对固定销售趋势字段的依赖。
- 前端接口契约补齐：`AnalysisResponse` 已声明后端返回的 `trace` 和 `steps`，但普通用户页面不展示内部调试细节。
- 统一检索评分基础层：metric、schema、SQL Memory 检索已复用文本相似、关键词命中、集合重合和加权评分工具，为后续 embedding / pgvector 混合检索打基础。
- EmbeddingAdapter 基础层：已提供 OpenAI-compatible embeddings 统一入口和 deterministic 本地 fallback，后续 schema、metric、SQL Memory 向量化必须通过该入口。
- Schema / Metric / SQL Memory Embedding 同步：可运行脚本把 `schema_metadata.embedding`、`metric_definitions.embedding` 和旧 `sql_memories` 的 question/sql embedding 写入 pgvector 字段，为后续混合检索准备向量资产。
- pgvector 混合检索：metric/schema retriever 会用 `EmbeddingAdapter` 生成问题向量，并结合 pgvector 候选分与原有关键词、文本和结构化分数排序。
- SQL Memory 混合检索：`semantic_similarity` 已优先使用 `sql_memories.question_embedding` 的 pgvector 分数，向量不可用时回退文本相似。
- 开发者调试 API：`GET /api/runs`、`GET /api/runs/{run_id}` 可查看运行记录和工具调用摘要。
- SQL Memory 调试 API：`GET /api/memories`、`GET /api/memories/{memory_id}` 可查看历史成功 SQL。
- 标准问题评估：`npm run eval:standard` 可运行 20 个 V1 标准问题，并生成 `eval/reports/latest_eval_report.json`。

## 项目结构

```text
frontend/   React + Vite + TypeScript 前端
backend/    FastAPI 后端、Agent 编排、工具函数、PostgreSQL 访问
docs/       计划文档、模块完成说明、handoff、数据库说明
eval/       标准问题评估集、评估脚本和最新报告
```

## V1 核心文档

- [架构说明](docs/architecture.md)
- [数据模型说明](docs/data_model.md)
- [Agent 工作流说明](docs/agent_workflow.md)
- [接口文档索引与阅读顺序](docs/api_index.md)
- [V1 接口文档](docs/api.md)
- [前后端接口映射文档](docs/api_frontend_mapping.md)
- [接口错误码与权限边界文档](docs/api_error_auth.md)
- [接口变更流程与版本维护文档](docs/api_change_process.md)
- [接口联调与 Smoke 示例文档](docs/api_smoke_examples.md)
- [SQL Guard 与只读执行说明](docs/sql_guard.md)
- [SQL Memory 机制说明](docs/sql_memory.md)
- [标准问题评估说明](docs/evaluation.md)

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
MODEL_PROVIDER=local
MODEL_BASE_URL=http://127.0.0.1:11434/v1
MODEL_NAME=local-sql-model
MODEL_API_KEY=change_me
MODEL_SQL_GENERATOR_ENABLED=false
EMBEDDING_PROVIDER=deterministic
EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_API_KEY=change_me
EMBEDDING_DIMENSIONS=1536
```

`MODEL_API_KEY=change_me` 是占位值，不会被 ModelAdapter 写入 Authorization header。真实密钥只放在本机 `backend/.env`，不要提交。

## 常用命令

```bash
npm run backend:test
npm run eval:standard
npm run test:e2e
npm run frontend:build
npm run backend:dev
npm run frontend:dev
py -3 backend/scripts/init_db.py
py -3 backend/scripts/sync_schema_metadata.py
py -3 backend/scripts/sync_embeddings.py
```

换库、导入新表或调整字段后，先运行：

```bash
py -3 backend/scripts/init_db.py
py -3 backend/scripts/sync_schema_metadata.py
py -3 backend/scripts/sync_embeddings.py
```

`sync_schema_metadata.py` 会扫描当前 PostgreSQL `public` schema 中的业务表字段，更新 `schema_metadata`，并保留已有人工字段说明。`sync_embeddings.py` 会为 schema 字段、指标口径和缺少向量的历史 SQL Memory 生成 embedding 并写入 pgvector 字段；默认本地配置使用 deterministic fallback，真实语义检索质量需要配置可用的 embedding provider。

## API 入口

接口文档阅读顺序见 [接口文档索引与阅读顺序](docs/api_index.md)。完整字段说明、请求示例、响应结构和错误边界见 [V1 接口文档](docs/api.md)。前端 API client 与后端接口字段关系见 [前后端接口映射文档](docs/api_frontend_mapping.md)。错误码、权限边界和上线前鉴权建议见 [接口错误码与权限边界文档](docs/api_error_auth.md)。接口字段、路径或权限发生变化时，按 [接口变更流程与版本维护文档](docs/api_change_process.md) 同步。手工联调命令和 smoke 检查点见 [接口联调与 Smoke 示例文档](docs/api_smoke_examples.md)。

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
- 成功查询会把 `parameters`（含 `days`、`granularity`、`metric`、`limit`）、最终 SQL、结果列和行数写入 `sql_memories`。
- 成功查询会同步 `question_embedding` 和 `sql_embedding`；检索时用问题向量召回历史 memory 候选。
- 普通用户不默认看到 SQL Memory 候选分数；开发者通过 `/api/memories` 和 `/api/runs` 查看。

## Model-backed SQL Generator 当前说明

- 模型调用统一通过 `backend/app/core/model_adapter.py`。
- embedding 调用统一通过 `backend/app/core/embedding_adapter.py`。
- schema/metric/SQL Memory 向量同步通过 `backend/app/services/embedding_sync_service.py` 和 `backend/scripts/sync_embeddings.py` 执行。
- schema/metric/SQL Memory 混合检索通过 `backend/app/tools/vector_retrieval.py` 查询 pgvector 候选；失败时自动退回原文本检索。
- SQL 生成 prompt 由 `backend/app/tools/model_sql_generator.py` 构造，只包含召回到的 schema 字段和指标口径，不使用全量数据库结构。
- 模型响应要求为 JSON，解析后输出 `GeneratedSql`。
- 模型生成的 SQL 当前不直接执行；后续接入 `/api/analyze` 时仍必须经过 SQL Validator、SQL Guard 和只读 Executor。
- `/api/analyze` 已预留 `MODEL_SQL_GENERATOR_ENABLED` 开关。默认 `false`，不调用模型；设为 `true` 后仅 `cold_path` 会尝试模型 SQL，模型失败或未返回 SQL 会回退到确定性生成路径。
- 普通用户前端不展示 prompt、模型原始输出、provider 或模型连接状态。
- 普通用户前端也不展示 embedding provider、向量状态或数据库连接状态。

## 标准问题评估

```bash
npm run eval:standard
```

评估数据集位于 `eval/datasets/standard_questions.jsonl`，当前包含 20 个 V1 标准问题。报告输出到 `eval/reports/latest_eval_report.json`，包含执行成功率、严格成功率、SQL 生成成功率、表命中率、关键词命中率、记忆命中率、复用成功率、平均延迟、路径占比、执行失败案例和断言失败案例。

当前评估区分两层结果：

- `execution_success_rate`：API 链路是否成功返回 SQL、通过 SQL Guard、得到结果。
- `strict_success_rate`：在链路成功基础上，SQL 是否命中预期表和关键词。

最近一次评估为 20/20 链路成功，严格成功率为 55%。SQL Memory fast_path 已加入关键表约束，记忆命中率从 100% 降为 60%，避免部分明显不匹配的历史 SQL 直接复用；剩余断言失败主要需要后续模型 SQL 生成或更完整的业务意图生成来修复。

## 当前验证

最近一次模块验证通过：

```bash
npm run frontend:build
npm run backend:test
npm run test:e2e
npm run eval:standard
```

## 开发约定

- 每次继续开发前先读取 `docs/handoff/current.md`。
- 每个模块先写 `docs/plans/YYYY-MM-DD-module-name.md`。
- 模块完成后写 `docs/modules/YYYY-MM-DD-module-name.md`。
- 通过相关测试后再提交并推送到 GitHub。
- 普通用户前端不默认展示模型、数据库连接、SQL 记忆评分、工具调用原始日志和评估报告。
