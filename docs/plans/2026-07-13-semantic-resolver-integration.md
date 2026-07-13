# Semantic Resolver Integration

## Goal

将 Phase 1 的版本化 Semantic Contract 接入现有意图和分析链路：唯一启用契约可绑定为结构化语义上下文；冲突契约才产生确定性澄清原因；未知但明确的自然语言候选保持开放式检索与模型生成路径。

## Scope

- 新增 `SemanticResolver`，按 display name、contract key 和 synonyms 解析启用契约。
- 扩展 `ParsedQuestionIntent`，承载绑定契约、冲突和澄清原因，不破坏既有 `semantic_metrics` / `semantic_dimensions`。
- 在 `AgentService` 和 follow-up 合并完成后统一调用 Resolver，再决定是否等待澄清或进入 Graph。
- 将安全的 resolved-contract 摘要透传至 retrieval context、SQL generator 和运行日志。
- 提供数据库无关聚焦测试，验证唯一、冲突、未知开放路径和后续澄清行为。

## Out of scope

- 不增加语义契约管理 API、前端页面或预置大量业务契约。
- 不让 Resolver 直接输出 SQL、绕过 QuerySpec、SQL Guard 或只读 Executor。
- 不实现完整 Query Planner、Trusted SQL、Inspector 或 Result Contract，它们由后续模块完成。

## Implementation steps

- [x] 定义 Resolver 输出与 intent 扩展字段。
- [x] 实现启用契约匹配、版本去重、冲突识别和开放式未知处理。
- [x] 接入 AgentService、Graph/Context/SQL Prompt 的最小数据流。
- [x] 编写聚焦测试、应用 migration 并运行全量后端测试。
- [ ] authenticated 评测对照、最终交付记录、commit、push。

## Validation plan

- `py -3 -m pytest backend/tests/test_semantic_resolver.py backend/tests/test_question_intent_parser.py backend/tests/test_conversation_service.py backend/tests/test_analysis_graph_sql_selection.py`
- `npm.cmd run backend:test`
- `npm.cmd run frontend:build`
- `npm.cmd run eval:standard -- --start 0 --limit 10 --report eval/reports/semantic_resolver_batch_001.json`

## Risks

- 预置契约不足时不得把未知概念当作错误或强制澄清。
- 多个契约命中时必须只报告会改变结果的冲突，避免用低置信度替代业务决策。
- 跨会话 follow-up 需要保留已解析的契约字段，否则补充条件后可能丢失业务口径。
