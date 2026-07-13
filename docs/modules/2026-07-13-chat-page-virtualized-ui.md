# ChatGPT 风格聊天页与虚拟消息窗口

## Completed behavior

- `ChatPage` 改为会话侧栏、消息主区域和固定输入区，移动端保留新对话入口；用户消息与助手消息使用不同气泡/内容层级，真实 SQL 和结果表继续按分析响应展示。
- 使用 `@tanstack/react-virtual` 按动态高度虚拟渲染当前消息窗口，不再为会话的每条保留消息创建完整 DOM。
- 会话详情消费 `has_more`、`next_before` 向上加载早期消息，并在插入前记录 scrollHeight、插入后补偿 scrollTop，避免读取历史时视线跳跃。
- 会话侧栏消费 `next_cursor` 加载更多会话；搜索仅过滤已加载会话，避免制造不存在的服务端搜索结果。
- 新会话从空态开始，建议问题只写入输入框；不作为模拟分析结果。
- `SqlPanel` 的 `sql` 改为必填，删除对 `frontend/src/data/mock.ts` 中固定 SQL 的回退依赖。

## Key decisions

- 虚拟化只覆盖当前 API 返回的消息窗口，完整会话仍通过上一模块的分页接口向上获取；不试图在浏览器内缓存全部历史。
- 本模块的“正在处理”只对应已有同步分析请求的 pending 状态，不伪造 token 流；真实 SSE 留给独立流式模块。
- SQL、rows 和错误只来源于当前 `AnalyzeResponse`；重新打开历史会话时当前持久化边界只恢复助手摘要，这一点不以 Mock 内容掩盖。

## API/data-contract impact

- 不新增 API；消费上一模块新增的 `ConversationListPage`、`has_more` 和 `next_before` 契约。
- 新增前端依赖 `@tanstack/react-virtual`。
- `SqlPanel` 调用方必须提供真实 SQL 字符串。

## Validation

- `npm.cmd run frontend:build`：通过。
- `http://127.0.0.1:3000`：现有 Vite 服务返回 HTTP 200。
- Mock 扫描：`ChatPage.tsx` 和 `SqlPanel.tsx` 无 `data/mock` 或 `finalSql` 引用。
- `git diff --check`：通过。
- `npm.cmd run test:e2e`：未通过。脚本 `backend/tests/smoke_api.py` 未登录调用 `/api/analyze`，本机 `AUTH_REQUIRED=true` 返回 401；该脚本与当前鉴权配置不匹配，未在本模块修改。

## Remaining risks and follow-up

- 需要后续浏览器登录 smoke 覆盖动态高度消息、向上加载后的滚动锚点和移动端布局。
- 图表仍将在 Result Contract/VisualizationSpec 模块接入真实 rows，聊天页暂时只展示表格。
- 实际 token 流、取消和最终消息持久化将在 SSE 模块实施。

## Delivery

- 本模块提交后补充 commit hash 与 push 结果；本地评测工件不纳入提交。
