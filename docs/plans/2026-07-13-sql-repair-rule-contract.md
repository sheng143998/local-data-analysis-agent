# SQL Inspector Repair Rule Contract

## Goal

将 SQL Inspector 的结构化 issue 转换为模型可直接执行、可复制的分类修复规则，改善生成 SQL 在 Query Plan 对齐、排行、时间和输出形态上的修复质量；不增加固定 SQL，也不绕过 Guard 或只读 Executor。

## Scope

- 为 Inspector issue 提供稳定的类别、消息和业务修复规则。
- 扩展 SQL generator/repair payload，按 issue 类别注入明确的修复步骤和验证条件。
- 增加 focused tests，覆盖每类规则的 payload 传递、未知类别的保守降级和 UTF-8 中文业务注释。

## Out of scope

- 不修改 Semantic Contract、Query Plan 生成、数据库 migration、公开 API 或评测报告。
- 不生成、执行或内置任何具体业务 SQL 模板。
- 不放宽 QuerySpec、SQL Guard、EXPLAIN 或只读 Executor 的安全边界。

## Implementation steps

- [x] 定义 Inspector issue 到 repair rule 的稳定映射。
- [x] 将分类规则接入 SQL repair prompt，并保留现有错误规则。
- [x] 增加 focused tests 并验证既有生成路径不变。
- [ ] 编写模块记录，更新 handoff，提交并推送。

## Validation plan

- `.venv\\Scripts\\python -m pytest backend/tests/test_sql_inspector.py backend/tests/test_model_sql_generator.py`。
- `git diff --check`。
- 不运行或修改 authenticated 评测报告；真实 benchmark 由主线集成后统一复测。

## Risks

- 模型可能仍忽略规则或输出无法解析的 SQL，因此规则只改善提示上下文，不能替代 Inspector、Guard 和 Executor。
- AST 无法确认复杂 CTE 的全部业务语义；未知类别必须使用保守通用规则，不能误放行。
