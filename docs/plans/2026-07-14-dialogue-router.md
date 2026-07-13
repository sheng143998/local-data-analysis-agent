# 安全 Dialogue Router 与通用聊天

## Goal

在现有会话中安全分流 `general_chat`、`data_analysis`、`clarification`、`explain_result` 和 `unsupported`，使普通聊天可使用独立 dialogue 模型，但仅数据分析进入 SQL Agent。

## Scope

- 新增独立 dialogue 模型配置与模型角色路由。
- 确定性安全 Router：待澄清会话优先续接；结果解释仅使用最近已保存摘要；明确数据问题进入 SQL；一般聊天使用 dialogue 模型；危险/越权请求受控拒绝。
- 通用对话只传用户消息、滚动摘要和有限最近会话文本，不传 schema、SQL、rows、prompt、密钥或运行追踪。
- 复用 `AnalyzeResponse` 与现有会话写入；前端显示通用聊天结果但不显示 SQL 区。
- 覆盖 Router 分类、SQL 隔离、模型不可用和会话持久化测试。

## Out of scope

- 不允许 dialogue 模型执行或生成可执行 SQL，不调用 Graph、Inspector、Guard 或 Executor。
- 不在本模块新增 token 流；SSE 只保留真实阶段和最终结果。
- 不向云端模型传递完整业务 schema、SQL、rows 或模型原始输出。

## Implementation steps

- [x] 定义对话角色、Router 和受控上下文构造器。
- [x] 新增 dialogue 模型配置/路由和通用聊天服务。
- [x] 将 AgentService 接入分流，保留澄清和数据分析路径。
- [x] 补 Router/服务/API focused tests，更新接口及前端说明。
- [x] 验证、模块记录、handoff、commit/push。

## Validation plan

- Router/AgentService focused pytest 覆盖五种角色、非数据问题不调用 Graph、结果解释不传 SQL/schema、模型失败安全退化。
- `npm.cmd run frontend:build` 与 SSE 现有回归。
- `git diff --check`，并运行 authenticated 50-case 前后对照或说明其未运行原因。

## Risks

- 语言模型分类不能作为 SQL 安全边界，路由必须有确定性数据意图规则并默认不访问数据库。
- 历史助手结果只存摘要，因此结果解释必须明确其信息范围，不能编造缺失指标。
- dialogue provider 未配置时必须降级为诚实提示，不应回退到 SQL 模型或发送敏感上下文。
