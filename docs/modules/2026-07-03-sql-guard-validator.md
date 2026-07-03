# 模块完成说明：SQL Guard / Validator

模块：SQL Guard / Validator

当前状态：已完成，确定性 SQL 安全校验和基础质量校验已实现，后端测试、smoke 和前端构建均通过。

业务逻辑：
- 模型或模板生成 SQL 后，必须先经过 Validator 和 Guard。
- Validator 负责语法、单语句、只读、白名单表、`SELECT *`、缺少 LIMIT 等规则检查。
- Guard 负责最终安全放行，并在安全 SELECT 缺少 LIMIT 时自动补充 LIMIT。
- 后续 SQL Executor 只能执行 Guard 输出的 `final_sql`。

关键代码：
- `backend/app/schemas/sql_validation.py`：定义 SQL 校验请求、结果和 Guard 输出契约。
- `backend/app/tools/sql_validation_tools.py`：实现 `validate_sql` 和 `guard_sql`。
- `backend/tests/test_sql_validation_tools.py`：覆盖安全 SELECT、`SELECT *`、写操作、多语句、非白名单表和自动 LIMIT。

数据契约：
- `SqlValidationRequest`: `sql`, `allowed_tables`, `max_rows`
- `SqlValidationResult`: `is_valid`, `errors`, `warnings`, `tables`, `normalized_sql`
- `SqlGuardResult`: `allowed`, `final_sql`, `errors`, `warnings`

验证：
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

风险/后续：
- 当前白名单表是静态默认值，后续应从 `schema_metadata` 或配置读取。
- 当前未做字段级存在性校验，后续应结合 schema metadata。
- 下一步应实现只读 SQL Executor，并强制只接受 Guard 后的 SQL。
