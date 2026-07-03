# 模块：Schema 表关系上下文

当前状态：本模块已完成关系推断、模型 SQL prompt 接入、完整验证、commit 和 push。提交信息为 `新增Schema表关系上下文并通过验证`，已推送到 GitHub。它不新增固定 SQL 模板，不改变普通用户前端，不改变模型默认开关。

业务逻辑：当系统召回多个表字段后，后端会从字段命名中推断高置信表关系，例如 `orders.id = payments.order_id`、`users.id = orders.user_id`、两个表共享 `order_id`。模型 SQL Generator 后续生成跨表查询时，可以优先使用这些关系，减少对固定问题模板的依赖。

关键代码：

- `backend/app/schemas/retrieval.py`：新增 `TableRelationshipContext`，并在 `RetrievalContext` 增加 `table_relationships`。
- `backend/app/tools/context_builder.py`：新增 `infer_table_relationships()`，基于同名键和 `table.id` 到 `<singular_table>_id` 的通用规则推断关系。
- `backend/app/tools/model_sql_generator.py`：把 `table_relationships` 写入 prompt JSON，并要求跨表查询优先使用高置信关系。
- `backend/tests/test_retrieval_tools.py`：覆盖上下文构建和通用 ID 约定推断。
- `backend/tests/test_model_sql_generator.py`：覆盖模型 prompt 包含关系上下文。

数据契约：

- `TableRelationshipContext.left_table`
- `TableRelationshipContext.left_column`
- `TableRelationshipContext.right_table`
- `TableRelationshipContext.right_column`
- `TableRelationshipContext.relationship_type`
- `TableRelationshipContext.confidence`
- `TableRelationshipContext.reason`
- `RetrievalContext.table_relationships` 默认空列表，后端内部使用，不进入普通用户页面。

验证：

- `py -3 -m pytest backend/tests/test_retrieval_tools.py backend/tests/test_model_sql_generator.py`，10 passed。
- `npm run backend:test`，135 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 字段命名不规范时无法推断关系，后续可从 PostgreSQL 外键元数据或业务关系配置补强。
- 本模块增强的是模型 SQL prompt 上下文，不直接改变默认 deterministic SQL 路径。
