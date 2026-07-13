# 对话路由澄清回归修复

## 完成行为

- `route_dialogue()` 将“看看最近情况”“最近经营情况”“业务概览”等有限的业务概览表达识别为 `data_analysis`。
- 这类问题仍先经过现有意图解析与澄清策略，缺少指标时会创建 `PendingClarification`；补充信息后再进入原有 SQL Graph。
- 问候和普通聊天仍走 `general_chat`，不会因为单独出现“最近”或“看看”而访问数据库。

## 根因和决策

- Dialogue Router 只识别了显式指标词，导致“看看最近情况”绕开解析器，直接由通用聊天服务回复。
- 该修复只加入完整的业务概览短语，而非扩展成宽泛关键词，以避免通用聊天被误送入数据分析链路。

## 验证

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_dialogue_router.py backend/tests/test_analysis_streaming.py backend/tests/test_conversation_service.py backend/tests/test_analysis_presenter.py backend/tests/test_result_contract_builder.py -q`：`28 passed, 1 warning`。
- `git diff --check`：通过。

## 剩余风险

- 业务概览短语当前为确定性有限集合；后续可在不放宽 SQL 安全边界的前提下用 Router 评估集扩充同义表达。

## 交付

- Commit：待生成并推送。
