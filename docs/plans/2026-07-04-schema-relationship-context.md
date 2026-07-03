# Schema 表关系上下文计划

## Goal

当前 Model-backed SQL Generator 的 prompt 只包含召回字段，没有告诉模型表之间如何连接。对于用户、流量、优惠券等跨表问题，模型即使拿到了字段，也容易少 join 或 join 错。本模块增加通用表关系上下文，从已召回的 schema 字段中推断高置信 join hints，帮助后续通用 SQL 生成，而不是继续新增固定 SQL 模板。

## Current task

当前正在做：本模块已完成实现、测试、文档更新、commit 和 push。

## Scope

包含：

- 在后端内部检索上下文中新增表关系结构。
- 基于召回字段通用推断表关系：
  - 同名 ID 字段关系，例如 `orders.order_id = payments.order_id`。
  - `table.id` 与其他表 `<singular_table>_id` 的关系，例如 `orders.id = payments.order_id`。
- 将表关系写入模型 SQL 生成 prompt。
- 增加 focused tests 和文档。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端展示。
- 不改变 `/api/analyze` 默认模型开关。
- 不直接提升标准评估严格成功率，除非后续启用真实模型并利用这些关系。

## Module boundary

上游输入：

- `MetricContext`
- `SchemaColumnContext`
- `build_retrieval_context(question)` 的 schema 召回结果。

下游输出：

- `RetrievalContext.table_relationships`
- `model_sql_generator` user prompt 中的 `table_relationships`

预计触达文件：

- `backend/app/schemas/retrieval.py`
- `backend/app/tools/context_builder.py`
- `backend/app/tools/model_sql_generator.py`
- `backend/tests/test_retrieval_tools.py`
- `backend/tests/test_model_sql_generator.py`
- `docs/agent_workflow.md`
- `docs/data_model.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-schema-relationship-context.md`

## Business logic

当系统召回了多个表字段时，后端会自动整理“可连接关系”给 SQL Generator。例如召回 `orders.id` 和 `payments.order_id` 后，prompt 会包含 `orders.id = payments.order_id`。这样换库或换表后，只要字段命名遵循常见 ID 约定，模型生成 SQL 时就能使用更新后的结构上下文。

## Data contract

新增后端内部结构：

- `TableRelationshipContext.left_table`
- `TableRelationshipContext.left_column`
- `TableRelationshipContext.right_table`
- `TableRelationshipContext.right_column`
- `TableRelationshipContext.relationship_type`
- `TableRelationshipContext.confidence`
- `TableRelationshipContext.reason`

`RetrievalContext.table_relationships` 默认空列表。

## Implementation steps

- [x] 读取 handoff、schema/context/model generator 代码和测试。
- [x] 创建计划文档。
- [x] 实现关系推断和 prompt 接入。
- [x] 增加 focused tests。
- [x] 更新文档、handoff 和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_retrieval_tools.py backend/tests/test_model_sql_generator.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and open questions

- 字段命名不规范时无法推断关系，后续可以从数据库外键元数据或人工业务关系表补强。
- 本模块只增强上下文，不改变默认模型开关，也不保证当前 deterministic SQL 严格成功率立即提升。
