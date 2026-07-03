# 模型 SQL Generator 上下文 Smoke 计划

## Goal

增强模型 SQL Generator 的可验证性，确保 prompt 确实包含召回字段、指标口径、表关系和复用计划，并验证模型输出不会绕过 SQL Guard / Validator。

## Current Task

当前正在做：模块已完成、已提交并推送。

## Scope

- 包含：模型 SQL Generator prompt payload 重构、单元测试、文档更新。
- 不包含：开启真实模型调用；新增固定 SQL 模板；改变普通用户前端；改变 `/api/analyze` 默认模型开关。

## Module Boundary

- 上游输入：`RetrievalContext`、`SqlReusePlan` 和用户问题。
- 内部处理：`model_sql_generator` 构造受控 JSON prompt，调用 `ModelAdapter`，解析模型 JSON。
- 下游输出：`GeneratedSql`，后续仍由 `analysis_graph` 送入 SQL Guard / Executor。

## Business Logic

当后续开启模型 SQL 生成时，模型只能看到已召回的 schema 字段、指标口径和表关系，不应拿到全量数据库结构或调试细节。测试要能证明模型 prompt 包含必要业务上下文，并证明模型返回编造字段时仍会被字段校验拦住。

## Data Contract

- 新增内部函数 `build_sql_generation_payload()`，返回 prompt JSON payload。
- API 响应不变。
- 数据库结构不变。
- 普通用户 UI 不展示 prompt、模型原始输出或 provider 状态。

## Implementation Steps

任务清单：
- [x] 创建模块计划文档。
- [x] 重构 prompt payload 构造。
- [x] 补充 prompt 内容和 Guard/Validator smoke tests。
- [x] 更新 README、Agent 工作流和模块文档。
- [x] 运行 focused tests 与完整验证。
- [x] 更新 handoff、提交并推送。

## Validation Plan

- `py -3 -m pytest backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py`
- `npm run backend:test`
- `npm run eval:standard`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks And Open Questions

- 本模块只加强模型路径验证，默认不开启真实模型，因此不会直接提升当前严格成功率。
- 真实模型质量仍依赖本地模型能力、embedding 质量和召回上下文质量。
