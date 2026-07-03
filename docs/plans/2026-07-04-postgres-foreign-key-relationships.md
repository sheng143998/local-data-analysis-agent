# PostgreSQL 外键表关系上下文计划

## Goal

让 Agent 在换库、换表后优先使用 PostgreSQL 真实外键生成跨表关系上下文，减少对固定 SQL 模板和字段命名猜测的依赖。

## Current Task

当前正在做：模块已完成、已提交，等待推送。

## Scope

- 包含：读取当前库 `public` schema 中的真实外键；仅返回已召回表字段相关的关系；真实外键使用更高置信度；失败时不影响分析链路。
- 不包含：新增固定 SQL 模板；普通用户界面展示外键、模型、数据库状态或调试 payload；变更业务表结构。

## Module Boundary

- 上游输入：`retrieve_schema()` 返回的 `SchemaColumnContext`。
- 内部处理：`context_builder` 聚合真实外键关系与命名推断关系。
- 下游输出：`RetrievalContext.table_relationships`，供 `model_sql_generator` prompt 和开发者运行日志摘要使用。
- 预计触达文件：
  - `backend/app/tools/context_builder.py`
  - `backend/tests/test_retrieval_tools.py`
  - `docs/agent_workflow.md`
  - `docs/data_model.md`
  - `README.md`

## Business Logic

业务分析人员换库或导入新表后，如果数据库里有外键约束，系统应自动理解表之间的连接关系。例如订单表和支付表存在外键时，模型 SQL 生成优先使用真实外键，而不是猜测字段名。没有外键或数据库不可用时，系统继续使用已有命名规则兜底，不中断问答。

## Data Contract

- `TableRelationshipContext.relationship_type` 新增可能值：`foreign_key`。
- `TableRelationshipContext.confidence`：真实外键默认高于命名推断。
- `TableRelationshipContext.reason`：记录来自 PostgreSQL 外键约束，但仅用于后端调试和 prompt，不进入普通用户页面。
- API 响应字段不变。

## Implementation Steps

任务清单：
- [x] 创建模块计划文档。
- [x] 实现 PostgreSQL 外键读取与关系合并。
- [x] 增加 focused tests 覆盖外键优先、兜底和数据库失败降级。
- [x] 更新 README、Agent 工作流、数据模型文档。
- [x] 运行 focused tests 和完整验证。
- [x] 写模块完成说明、更新 handoff、提交并推送。

## Validation Plan

- `py -3 -m pytest backend/tests/test_retrieval_tools.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks And Open Questions

- 部分用户库可能没有声明外键，只能继续依赖命名推断和 schema/metric 检索。
- 本模块只提供关系上下文，不直接提升默认确定性 SQL 生成覆盖率；后续还需要推进模型 SQL 生成和评估诊断。
