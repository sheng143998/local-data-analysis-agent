# 模块：模型 SQL Generator 上下文 Smoke

当前状态：本模块已完成代码开发、文档更新、完整验证、commit 和 push。提交信息为 `增强模型SQL生成上下文Smoke并通过验证`，已推送到 GitHub。该模块不新增固定 SQL 模板，不开启真实模型默认路径，不改变普通用户前端，也不展示 prompt 或模型原始输出。

业务逻辑：后续启用模型 SQL 生成时，模型只能基于本次召回的 schema 字段、指标口径、复用计划和表关系上下文生成 SQL。本模块把 prompt payload 抽成可测试结构，并补充安全 smoke，证明模型即使返回编造字段，也会在执行前被 SQL Validator / SQL Guard 拦截。

关键代码：

- `backend/app/tools/model_sql_generator.py`
  - 新增 `build_sql_generation_payload()`，返回结构化 prompt payload。
  - `_user_prompt()` 复用该 payload 后序列化为 JSON，保持模型调用协议不变。
  - payload 包含 `question`、`reuse_plan`、`allowed_tables`、`allowed_fields`、`metrics`、`schema_fields`、`table_relationships` 和 `requirements`。
- `backend/tests/test_model_sql_generator.py`
  - 新增结构化 payload 契约测试，覆盖指标、字段、表关系、复用计划和 Validator/Guard 要求。
  - 新增模型编造字段 smoke：模型返回 `orders.not_exists` 时，`guard_sql(..., schema_fields=context.fields)` 会阻断执行。

数据契约：

- 新增内部函数契约：`build_sql_generation_payload(question, retrieval_context, reuse_plan) -> dict[str, Any]`。
- API 响应不变。
- 数据库结构不变。
- `GeneratedSql` 契约不变。

验证：

- `py -3 -m pytest backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py`，11 passed。
- `npm run backend:test`，149 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 本模块只增强模型路径测试和 prompt 可验证性，默认仍不开启真实模型，因此不会直接提升当前严格成功率。
- 真实模型质量仍依赖本地模型能力、embedding 质量、schema/metric 召回质量和后续评估驱动修复。
