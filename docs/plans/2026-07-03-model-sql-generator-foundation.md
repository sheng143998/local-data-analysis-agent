# Model-backed SQL Generator 基础层计划

当前正在做：Model-backed SQL Generator 基础工具已完成实现、测试和文档更新，等待提交并推送。

## Goal

让后续“问题到 SQL”逐步摆脱固定模板。该模块把 SQL Generator 的模型调用骨架建立起来：使用已召回的 schema 和指标口径构造受控 prompt，通过统一 ModelAdapter 调用模型，并解析结构化 SQL 响应。

## Scope

- 包含：
  - 新增模型 SQL 生成工具。
  - prompt 只包含已召回 schema/metric，不塞全量数据库结构。
  - 要求模型输出 JSON。
  - 解析 SQL、解释、表、指标和 warnings。
  - 增加无真实模型服务的单元测试。
  - 更新 README、模块说明和 handoff。
- 不包含：
  - 在 `/api/analyze` 中启用模型生成 SQL。
  - 直接执行模型生成的 SQL。
  - 真实流式输出。
  - embedding 检索。

## Module Boundary

- 上游输入：用户问题、`RetrievalContext`、`SqlReusePlan`。
- 核心处理：构造 OpenAI-compatible messages，调用 `ModelAdapter.chat()`，解析 JSON。
- 下游输出：`GeneratedSql`，其 SQL 后续必须进入 Validator / Guard / Executor。

## Business Logic

- 对普通用户不可见：prompt、模型原始输出、provider、模型名称不展示在前端。
- 对开发者可追踪：后续接入 Agent 图时可把生成路径、warnings 和模型调用摘要写入 `tool_calls`。
- 不允许模型使用未召回表字段，不允许输出 DDL/DML，不允许 `SELECT *`。

## Data Contract

- 输入：
  - `question: str`
  - `retrieval_context: RetrievalContext`
  - `reuse_plan: SqlReusePlan`
- 输出：
  - `GeneratedSql.path`: `model_generate` / `model_rewrite` / `model_error`
  - `GeneratedSql.sql`
  - `GeneratedSql.warnings`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 实现 prompt builder、JSON parser 和 adapter-backed generator。
- [x] 添加单元测试。
- [x] 更新 README、模块完成文档和 handoff。
- [~] 运行验证并提交推送。

## Validation Plan

- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and Open Questions

- 该模块只生成 SQL 文本，不执行；接入主链路时仍必须经过 Validator 和 Guard。
- 模型质量未验证，后续需要标准问题评估集来衡量成功率。
