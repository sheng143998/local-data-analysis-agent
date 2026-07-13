# 对话路由澄清回归修复

## Goal

确保在数据分析产品语境中，具有分析意图但缺少指标的概览请求进入既有澄清链路，而不是被误判为通用聊天。

## Scope

- 为明确的概览分析表达增加受控、确定性的 data-analysis 路由规则。
- 保持问候、闲聊和非数据问题不进入 Graph。
- 补充 Router 回归测试，并回归会话续接、SSE、图表和分页 focused tests。

## Out of scope

- 不把任意含“最近”或“看看”的通用对话送入 SQL Agent。
- 不改变澄清策略、SQL Guard、Executor、模型配置或数据契约。

## Implementation steps

- [x] 复现并定位路由将“看看最近情况”分到 general_chat 的原因。
- [x] 增加有限的概览分析短语规则与单元测试。
- [x] 回归会话澄清、Router、SSE、分页和图表 focused tests。
- [x] 更新模块记录、handoff、提交并推送。

## Validation plan

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_dialogue_router.py backend/tests/test_analysis_streaming.py backend/tests/test_conversation_service.py backend/tests/test_analysis_presenter.py backend/tests/test_result_contract_builder.py -q`。
- `git diff --check`。

## Risks

- 概览短语集合过宽会把普通聊天误路由到 SQL；规则必须限定为数据分析产品中的完整业务概览表达，且仍由意图解析决定是否澄清。
