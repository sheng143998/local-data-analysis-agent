# 模块：PostgreSQL 外键表关系上下文

当前状态：本模块已完成代码开发、文档更新、完整验证、commit 和 push。提交信息为 `接入PostgreSQL外键关系上下文并通过验证`，已推送到 GitHub。该模块不新增固定 SQL 模板，不改变普通用户前端，也不展示数据库连接状态或内部关系评分。

业务逻辑：用户换库、导入新表或调整表结构后，如果 PostgreSQL 中存在真实外键，Agent 会优先把这些外键作为跨表 join hints 提供给 SQL Generator。没有外键、外键字段未被召回或数据库元数据读取失败时，系统自动退回原有字段命名推断，不中断数据问答。

关键代码：

- `backend/app/tools/context_builder.py`
  - `build_retrieval_context()` 调用 `infer_table_relationships(..., include_database_foreign_keys=True)`。
  - `infer_table_relationships()` 先加载真实外键关系，再追加同名键和 `<table>_id` 命名推断关系；重复关系以外键为准。
  - `_load_postgres_foreign_key_relationships()` 从 `information_schema.table_constraints`、`key_column_usage` 和 `constraint_column_usage` 读取 `public` schema 外键。
  - `_relationship_columns_are_recalled()` 保证只有已召回字段相关的外键进入上下文，避免 prompt 使用未允许字段。
- `backend/tests/test_retrieval_tools.py`
  - 覆盖真实外键优先、数据库异常降级、只保留已召回字段关系。

数据契约：

- API 响应字段不变。
- `RetrievalContext.table_relationships` 仍为后端内部上下文字段。
- `TableRelationshipContext.relationship_type` 新增实际取值 `foreign_key`。
- 外键关系置信度为 `0.98`，高于命名推断的 `same_key` 和 `id_to_foreign_key`。
- `reason` 记录 PostgreSQL 外键约束名，仅用于后端 prompt 和开发者调试摘要，不进入普通用户页面。

验证：

- `py -3 -m pytest backend/tests/test_retrieval_tools.py`，8 passed。
- `npm run backend:test`，145 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 如果用户数据库没有声明外键，本模块只能使用命名推断兜底。
- 本模块增强的是模型 SQL 生成上下文，不会直接扩大默认确定性 SQL 生成覆盖面；后续仍应推进模型路径 smoke、评估失败 trace 关联或更通用的生成策略。
