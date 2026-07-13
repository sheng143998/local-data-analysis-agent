# ChatGPT 风格聊天页与虚拟消息窗口

## Goal

将数据问答页改造为以会话为中心的 ChatGPT 风格界面，消费分页会话 API，避免历史过长导致整个页面和 DOM 无限增长。

## Scope

- 引入 `@tanstack/react-virtual`，对当前会话消息使用动态高度虚拟列表。
- 消费 `has_more` / `next_before` 向上加载早期消息，并保持滚动锚点。
- 消费会话 `next_cursor` 加载更多会话；本地搜索只过滤已加载会话，后续可扩展服务端搜索。
- 重构 ChatPage 为会话侧栏、消息气泡、固定输入区、结果摘要/SQL/表格区和新会话空态。
- 删除聊天路径中 `SqlPanel` 对 `data/mock` 的默认 SQL 依赖。

## Out of scope

- 不实现 SSE/token 流、ECharts 图表、会话服务端搜索或独立消息表。
- 不更改 SQL 分析、会话 API 契约、鉴权、记忆或模型路由。
- 不把示例提示词当作 API 返回数据或业务结果。

## Implementation steps

- [x] 安装虚拟列表依赖并实现消息窗口渲染、加载早期消息和滚动锚点。
- [x] 实现会话分页加载、搜索与新会话切换。
- [x] 重构 ChatPage 布局和交互状态，保留真实分析响应、错误和 SQL/结果表展示。
- [x] 移除 `SqlPanel` Mock 默认值，补充前端类型安全。
- [ ] 运行前端 build，启动开发服务并做浏览器 smoke；更新文档、handoff、commit/push。

## Validation plan

- `npm.cmd run frontend:build`。
- 浏览器 smoke：登录后可打开聊天页、新建会话、打开历史、发送问题、加载更多会话/消息；长消息列表非空且不重叠。
- `git diff --check` 与 UTF-8 文档读取。

## Risks

- 动态高度虚拟化需要在插入早期消息后修正 scrollTop，防止用户视线跳跃。
- 当前会话详情仅保存摘要 response，重开历史时不保证恢复完整 SQL/rows；这是现有持久化边界，图表和完整结果持久化另行处理。
- Vite dev server 只用于本地 smoke，不能把环境 URL 或会话 cookie 写入提交。
