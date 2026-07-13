# 会话分页与消息窗口契约

## Completed behavior

- `GET /api/conversations` 现在返回 `ConversationListPage`，包含 `items` 和不透明 `next_cursor`；使用更新时间和会话 ID 作为稳定排序键，支持避免同一时间点的跨页重复。
- `GET /api/conversations/{conversation_id}` 默认只返回最近 50 条按时间正序消息，可使用 `limit` 和 `before` 向前加载；响应包含 `has_more` 和 `next_before`。
- InMemory、Redis 和 PostgreSQL 会话列表路径统一接收分页排序键；Redis 仍以 PostgreSQL 持久化副本为列表来源。
- 前端 `analysisClient` 和 `ChatPage` 已适配会话列表分页对象；当前页面继续显示最近消息窗口，为下一模块的虚拟列表和“加载更多”交互提供兼容契约。

## Key decisions

- cursor 只编码 `updated_at` 和会话 ID，不编码 owner、标题或消息内容。
- 消息窗口使用最早已加载消息的 ID 作为 `before`，返回的消息保持时间正序，前端可在顶部插入更早内容并保持滚动锚点。
- 当前会话仍保存为 JSONB 状态；本模块降低 API 和浏览器单次负载，不宣称解决超大消息状态的数据库读取成本。

## API/data-contract impact

- `GET /api/conversations` 从数组改为 `{ items, next_cursor }`，前端 API 类型和映射文档已同步。
- `GET /api/conversations/{conversation_id}` 新增 `limit`、`before` 查询参数与 `has_more`、`next_before` 响应字段，owner 隔离规则不变。
- 未修改 `/api/analyze`、SQL 生成、Guard、Executor、模型路由或数据库迁移。

## Validation

- `.venv\Scripts\python.exe -m pytest backend/tests/test_conversation_service.py backend/tests/test_conversation_store.py -q`：`13 passed, 1 warning`。
- `npm.cmd run frontend:build`：通过。
- `git diff --check`：通过。
- API 文档、前端 client 与类型已同步；测试覆盖 cursor 无效、跨页无重复、消息窗口无重复、owner 隔离和 Redis repository adapter。

## Remaining risks and follow-up

- 下一前端模块需要消费 `next_cursor`、`has_more` 和 `next_before`，实现会话搜索、虚拟列表、向上加载与滚动锚点。
- JSONB 中最多保留 200 条消息；若要支持更长可检索历史，需要独立规划 `conversation_messages` 迁移。
- 当前没有流式 API，后续 SSE 模块不得把同步 SQL 运行伪装成 token 流。

## Delivery

- 本模块提交完成后补充 commit hash 与 push 状态；已有本地评测工件不会纳入本次提交。
