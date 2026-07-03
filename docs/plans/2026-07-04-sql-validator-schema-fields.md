# SQL Validator 字段存在性校验计划

## Goal

当前 SQL Validator 已能拦截写操作、非白名单表和 `SELECT *`，但还没有基于真实 schema 校验字段是否存在。后续模型 SQL 生成启用后，如果模型编造字段，最好在执行前由 Guard 拦截。本模块接入 `schema_metadata` 字段集合，增强通用安全链路，不新增固定 SQL 模板。

## Current task

当前正在做：本模块已完成实现、测试、文档更新、commit 和 push。

## Scope

包含：

- 为 `SqlValidationRequest` 增加可选 `schema_fields`，用于测试或上游显式传入字段集合。
- 默认从 `schema_metadata` 加载当前 SQL 涉及表的字段集合。
- 校验显式字段、带别名字段和单表未限定字段。
- 元数据不可用时降级 warning，不阻断查询。
- 更新 SQL Guard 文档、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端。
- 不做业务语义判断。
- 不解析复杂表达式的全部血缘，只覆盖 V1 常见 SELECT/JOIN/WHERE/GROUP BY/ORDER BY 字段引用。

## Module boundary

上游输入：

- `SqlValidationRequest.sql`
- `SqlValidationRequest.allowed_tables`
- `SqlValidationRequest.schema_fields`
- PostgreSQL `schema_metadata`

下游输出：

- `SqlValidationResult.errors`
- `SqlValidationResult.warnings`
- `SqlGuardResult.allowed`

预计触达文件：

- `backend/app/schemas/sql_validation.py`
- `backend/app/tools/sql_validation_tools.py`
- `backend/tests/test_sql_validation_tools.py`
- `backend/tests/test_sql_execution_tools.py`
- `docs/sql_guard.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-sql-validator-schema-fields.md`

## Business logic

当 SQL 引用不存在的字段时，Guard 应在执行前阻断，例如 `SELECT missing_column FROM orders`。当 schema metadata 暂不可用时，Validator 应给出 warning 并保留当前只读安全拦截能力，不因为元数据服务异常导致所有查询不可用。

## Data contract

新增请求字段：

- `SqlValidationRequest.schema_fields: list[str] | None`

格式：

- `table.column`

新增错误：

- `字段不存在或未在 schema_metadata 中登记：orders.missing_column`

新增 warning：

- `schema_metadata 字段校验不可用：...`

## Implementation steps

- [x] 读取 handoff、Validator、Guard、Executor 测试和 SQL Guard 文档。
- [x] 创建计划文档。
- [x] 实现字段集合加载和字段引用校验。
- [x] 更新测试。
- [x] 更新文档、handoff 和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_sql_validation_tools.py backend/tests/test_sql_execution_tools.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and open questions

- SQL 解析中复杂 CTE、子查询和表达式别名的字段血缘后续还可继续增强。
- 依赖 `schema_metadata` 已同步；换库后应运行 `context:refresh` 或 `sync_schema_metadata.py`。
