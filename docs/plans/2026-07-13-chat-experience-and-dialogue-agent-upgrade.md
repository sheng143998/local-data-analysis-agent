# ChatGPT 体验与通用对话 Agent 升级

## Goal

将当前同步数据问答页升级为可扩展的 ChatGPT 风格会话体验：真实会话分页和长历史治理、真实流式输出、Result Contract 驱动的 ECharts 图表、移除前端 Mock 展示，并在同一会话内安全路由通用聊天、澄清、结果解释和 SQL 数据分析。

## Scope

- 为会话列表和消息详情增加稳定分页契约，支持按页加载和虚拟列表，不一次渲染完整历史。
- 重构聊天页为可折叠会话栏、固定输入区、消息气泡、分层结果区和可中断流式状态。
- 从 `AnalysisResponse` 派生确定性 `VisualizationSpec`，使用真实 `rows` 生成折线图、柱状图、环形图、指标卡或表格。
- 将已有 `frontend/src/data/mock.ts` 的业务展示逐步替换为真实 API、明确空态或开发者专用页面。
- 新增安全 Dialogue Router：`general_chat`、`data_analysis`、`clarification`、`explain_result` 和 `unsupported` 分流；只有 `data_analysis` 可进入现有 SQL Agent。
- 增加 POST SSE 流协议和前端 `ReadableStream` 消费；只流式传输真实模型文本和真实执行阶段，不制造伪进度。
- 分别评测前端交互、路由准确性、非数据问题不调用 SQL、澄清续接，以及 authenticated 50-case 数据质量不回退。

## Out of scope

- 不允许任何对话模型直接执行 SQL、绕过 Semantic Contract、Query Plan、Inspector、SQL Guard 或只读 Executor。
- 不把完整 schema、SQL、用户原始数据或密钥默认发送给云端对话模型；数据分析仍遵从现有批准的模型路由边界。
- 不在本轮实现多租户、OAuth、MFA、多人协作或后台异步任务队列。
- 不以静态模拟图表、假 token 打字或固定业务回答替代真实 API/模型行为。

## Implementation steps

- [x] 盘点现有 ChatPage、会话存储、Mock 组件、ECharts 依赖和模型路由边界。
- [x] 建立会话列表 cursor 分页和消息窗口分页 API，保持 owner 隔离和 Redis/PostgreSQL 回退。
- [x] 将 ChatPage 改为 ChatGPT 风格 shell：会话搜索/分页、消息虚拟窗口、向上加载、稳定滚动锚点和响应式布局。
- [x] 新增 `VisualizationSpec` 和真实 ECharts 结果组件，清理数据问答相关 Mock。
- [x] 新增 `POST /api/analyze/stream` 事件协议、取消处理和前端真实流式消费。
- [ ] 实现 Dialogue Router 和独立 `dialogue` 模型角色，统一使用现有会话和三层记忆。
- [ ] 新增后端/前端/e2e/router/50-case 回归，逐模块写记录、提交并推送。

## Validation plan

- 分页模块：conversation service/API focused pytest，覆盖 owner 隔离、cursor、空页和前后页无重复。
- 前端模块：`npm.cmd run frontend:build`，必要时 Playwright 验证长会话不无限增长、滚动加载、移动端布局和图表非空。
- 流式模块：后端 SSE contract tests、前端 stream parser tests、取消与最终持久化 smoke。
- 路由模块：数据问题、闲聊、结果解释、澄清补充、拒绝和模型不可用的 focused tests；authenticated 50-case 对照不回退。
- 每个模块都验证 UTF-8 文档、`git diff --check`，并在通过后独立 commit/push。

## Risks

- 现有会话把最多 200 条消息序列化在 JSONB 中；分页初期只能降低前端传输/渲染压力，后续高容量场景需要迁移独立 `conversation_messages` 表。
- FastAPI 同步 SQL 运行链路不能伪装成 token 流；必须明确区分模型 token、真实 Agent 阶段和最终结果事件。
- 云端对话模型需单独配置和脱敏边界，不能默认继承 SQL 模型输入。
- 图表自动选择必须由 Result Contract 的确定性规则决定；高基数类别、混合单位和不可计算结果必须退回表格或指标卡。
