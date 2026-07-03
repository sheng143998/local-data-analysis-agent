# Model SQL Generator cold_path 接入完成说明

模块：Model SQL Generator cold_path 配置开关接入

当前状态：已完成实现、测试和文档更新，等待提交并推送到 GitHub。

业务逻辑：

- `/api/analyze` 现在具备可选模型 SQL 生成入口，但默认关闭，避免本地未配置模型服务时影响现有真实 PostgreSQL 闭环。
- 当 `MODEL_SQL_GENERATOR_ENABLED=true` 且 SQL Memory 规划结果为 `cold_path` 时，analysis graph 会尝试调用 `generate_sql_with_model()`。
- 模型返回 SQL 后，仍进入现有 `guard_sql()` 和 `execute_guarded_sql()`，不会绕过安全链路。
- 如果模型调用失败、超时或没有返回 SQL，系统会退回现有确定性生成路径，普通用户继续得到稳定结果。
- `fast_path` 和 `rewrite_path` 不调用模型，继续优先复用历史成功 SQL 或确定性改写。

关键代码：

- `backend/app/core/config.py`
  - 新增 `MODEL_SQL_GENERATOR_ENABLED` 布尔配置读取。
- `backend/app/agents/analysis_graph.py`
  - 新增 `_select_generated_sql()`，集中选择 SQL 生成路径。
  - 开启模型时仅 `cold_path` 调用 `generate_sql_with_model()`。
  - 模型失败时回退到 `generate_or_rewrite_sales_sql()` 并附加 warning。
  - 原有 Guard、Executor、Presenter、Run Logger 链路保持不变。
- `backend/tests/test_analysis_graph_sql_selection.py`
  - 覆盖默认关闭模型、开启后 cold_path 使用模型、模型失败回退、rewrite_path 不调用模型。
- `backend/.env.example`
  - 新增 `MODEL_SQL_GENERATOR_ENABLED=false`。

数据契约：

- 配置：
  - `MODEL_SQL_GENERATOR_ENABLED=false|true`
- 内部输出：
  - `GeneratedSql.path` 可为 `model_generate` 或现有确定性路径。
  - `GeneratedSql.warnings` 在回退时包含模型失败说明。
- 日志：
  - `tool_calls` 中 SQL 生成步骤记录 `generation_path`。

验证：

- `npm run backend:test`：68 passed，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 模型生成默认仍关闭，尚未用真实模型服务跑标准问题集。
- 后续需要在本地模型配置稳定后开启开关，运行评估集并记录 SQL 生成成功率、Guard 通过率和失败样例。
- 当前 Graph 仍保留确定性回退路径，后续应逐步把更多 cold_path 问题交给模型和评估体系验证。
