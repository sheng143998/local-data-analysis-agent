# Model-backed SQL Generator 基础工具完成说明

模块：Model-backed SQL Generator 基础工具

当前状态：已完成实现、测试和文档更新，等待提交并推送到 GitHub。

业务逻辑：

- 后续当 SQL Memory 无法高置信复用时，系统需要通过模型生成 SQL，而不是继续堆固定业务模板。
- 本模块新增模型 SQL 生成工具：使用召回到的 `RetrievalContext` 和 `SqlReusePlan` 构造 prompt，通过统一 `ModelAdapter` 调用 OpenAI-compatible 模型，并解析 JSON 格式 SQL。
- 该工具只生成 SQL 文本，不执行 SQL。后续接入主链路时，模型生成 SQL 仍必须经过 SQL Validator、SQL Guard 和只读 Executor。
- 普通用户界面不展示 prompt、模型原始输出、provider、模型名称或工具 payload。

关键代码：

- `backend/app/tools/model_sql_generator.py`
  - `build_sql_generation_messages()`：构造 system/user messages，要求模型只生成 PostgreSQL SELECT、禁止 `SELECT *`、只能使用召回字段。
  - `generate_sql_with_model()`：调用 `ModelAdapter.chat()`，要求 JSON response format，并返回 `GeneratedSql`。
  - `parse_model_sql_response()`：解析模型 JSON，提取 `sql`、`reasoning`、`tables`、`metrics` 和 `warnings`。
- `backend/app/schemas/sql_generation.py`
  - 扩展 `SqlGenerationPath`，新增 `model_generate`、`model_rewrite`、`model_error`。
  - `GeneratedSql` 新增模型 provider、model、latency 元数据字段，默认不展示给普通用户。
- `backend/tests/test_model_sql_generator.py`
  - 覆盖 prompt 是否只使用召回上下文、JSON SQL 解析、`SELECT *` warning、成功生成和模型错误路径。

数据契约：

- 输入：
  - `question`
  - `RetrievalContext.metrics`
  - `RetrievalContext.schema_columns`
  - `SqlReusePlan.path_type`
  - `SqlReusePlan.selected_sql`
- 输出：
  - `GeneratedSql.path`
  - `GeneratedSql.sql`
  - `GeneratedSql.warnings`
  - `GeneratedSql.model_provider`
  - `GeneratedSql.model_name`
  - `GeneratedSql.model_latency_ms`

验证：

- `npm run backend:test`：64 passed，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 当前尚未把模型生成 SQL 接入 `/api/analyze` 主链路。
- 后续接入时必须记录工具调用摘要，并确保模型 SQL 经过 Validator / Guard / Executor。
- 需要标准问题评估集来衡量模型 SQL 生成成功率和失败样例。
