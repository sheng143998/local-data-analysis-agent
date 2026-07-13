# Clarification Policy

## Goal

以独立确定性 Policy 统一决定是否追问，基于结构化缺失槽位、契约冲突和用户动作，而非模型置信度或词表命中。

## Scope

- 新增结构化 ClarificationDecision 和纯 ClarificationPolicy。
- Resolver 只输出契约/冲突事实；AgentService 根据 Policy 决策进入 pending 或 Graph。
- 保持旧 pending 状态兼容，并为冲突和真正缺失指标补充测试。

## Out of scope

- 不替换云端自然追问模型、不更改 SQL 生成、Guard、Executor 或前端 API。

## Implementation steps

- [x] 实现 Policy 输入、决策和结构化原因。
- [x] 收回 Resolver 中的澄清文本，接入 AgentService/pending。
- [x] 补测试并运行后端全量。
- [ ] authenticated 评测抽样、commit、push。

## Validation plan

- `py -3 -m pytest backend/tests/test_clarification_policy.py backend/tests/test_semantic_resolver.py backend/tests/test_conversation_service.py`
- `npm.cmd run backend:test`
- authenticated 评测抽样。

## Risks

- 旧会话 pending 只有 `metrics`/`time_range`，新 decision 必须可降级读取。
- Policy 不得把未知明确概念或低置信度当作缺失指标。
