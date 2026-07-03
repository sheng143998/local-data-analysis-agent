# 模块：SQL Validator 字段存在性校验

当前状态：本模块已完成字段存在性校验、完整验证、commit 和 push。提交信息为 `接入SQL字段存在性校验并通过验证`，已推送到 GitHub。它不新增固定 SQL 模板，不改变普通用户前端。

业务逻辑：当模型或记忆复用产出的 SQL 引用了不存在字段时，Validator 会在执行前阻断。例如 `SELECT missing_column FROM orders` 会返回 `字段不存在或未在 schema_metadata 中登记：orders.missing_column`。如果 `schema_metadata` 暂不可用，Validator 会降级为 warning，保留只读、安全表白名单和 `SELECT *` 等基础拦截能力。

关键代码：

- `backend/app/schemas/sql_validation.py`：`SqlValidationRequest` 新增可选 `schema_fields`，用于测试或上游显式传入字段集合。
- `backend/app/tools/sql_validation_tools.py`：
  - `_resolve_schema_fields()`：优先使用请求传入字段，否则从 `schema_metadata` 加载。
  - `_validate_field_references()`：校验 SQL 中字段是否存在。
  - `_table_aliases()` / `_output_aliases()`：处理 JOIN 表别名和 `ORDER BY` 输出别名。
  - `guard_sql()` 支持透传 `schema_fields`。
- `backend/tests/test_sql_validation_tools.py`：覆盖缺字段拦截、JOIN 别名字段通过、输出别名通过、元数据不可用 warning。
- `backend/tests/test_sql_execution_tools.py`：将 runtime error 用例改为真实执行期错误，避免与字段校验冲突。

数据契约：

- `SqlValidationRequest.schema_fields: list[str] | None`
- 字段格式为 `table.column`。
- 新增错误：`字段不存在或未在 schema_metadata 中登记：...`
- 新增 warning：`schema_metadata 字段校验不可用：...`

验证：

- `py -3 -m pytest backend/tests/test_sql_validation_tools.py backend/tests/test_sql_execution_tools.py`，13 passed。
- `py -3 -m pytest backend/tests/test_sql_validation_tools.py backend/tests/test_sql_execution_tools.py backend/tests/test_api.py::test_analyze_supports_repeat_purchase_rate_slice`，14 passed，1 个 `StarletteDeprecationWarning`。
- `npm run backend:test`，139 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 复杂 CTE、子查询和表达式血缘后续还可增强。
- 换库或改表后需要刷新 `schema_metadata`，否则字段校验可能基于旧字段集合。
