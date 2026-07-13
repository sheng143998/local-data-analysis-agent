# Clarification Policy

## Completed behavior

- `ClarificationPolicy` 以缺失业务对象和语义契约冲突决定 `execute`/`clarify`，不以模型置信度或词表命中触发追问。
- Resolver 仅绑定契约并报告冲突，不再拥有用户可见澄清文案。
- AgentService 在 Resolver 后应用 Policy；旧 pending 会话保持原有字段和持久化格式。

## Validation

- focused `15 passed, 1 warning`。
- 后端全量 `237 passed, 1 warning`。

## Remaining risks

- 自然追问生成和多次无进展熔断将随下一轮会话状态增强实现。
- authenticated 评测对照待与下一 SQL/Planner 模块合并运行，避免本地模型长耗时重复消耗。
