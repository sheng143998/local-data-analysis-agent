# 会话分页与消息窗口契约

## Goal

为 ChatGPT 风格前端提供可稳定加载的会话列表和消息窗口，避免历史会话增长后一次返回或渲染所有记录。

## Scope

- `GET /api/conversations` 返回带不透明 cursor 的分页对象。
- `GET /api/conversations/{id}` 支持 `limit` 和 `before`，按时间正序返回一段消息窗口并提供继续向前加载的信息。
- 保持 owner 隔离、会话 TTL、Redis/PostgreSQL/InMemory store 行为一致。
- 同步前端 API 类型和当前 ChatPage 的会话列表读取；当前页面仍只显示最新消息窗口，虚拟列表和“加载更多”按钮由下一 UI 模块实现。
- 同步 API 文档、测试和 handoff。

## Out of scope

- 不迁移 `conversation_states.state` 中的 JSONB 消息为独立消息表。
- 不修改会话压缩、长期记忆、SQL 分析、模型路由或流式协议。
- 不删除历史会话或调整数据保留时间。

## Implementation steps

- [x] 定义 cursor/page/message-window Pydantic 契约。
- [x] 实现 InMemory、PostgreSQL 和 Redis 回退路径的会话列表分页。
- [x] 实现消息窗口截取并返回 `has_more` 与 `next_before`。
- [x] 同步 API 路由、前端类型/client/ChatPage 与 API 文档。
- [x] 新增 focused tests，运行前端构建和 diff 检查。
- [x] 写模块记录、更新 handoff、commit 并 push。

## Validation plan

- `pytest backend/tests/test_conversation_service.py`，覆盖 owner 隔离、列表 cursor、消息窗口、空 cursor、无效 cursor 和无重复窗口。
- `npm.cmd run frontend:build`。
- 核对 API 文档与前端 client 类型，执行 `git diff --check`。

## Risks

- JSONB 会话状态仍需读取完整对象，当前模块主要降低 API 响应和浏览器 DOM 压力；超大规模历史需后续单独迁移消息表。
- cursor 必须同时含更新时间与会话 ID，避免同一毫秒更新时间下分页重复或漏项。
- 消息窗口 token 只表示消息 ID，不应泄漏 owner、内容或数据库内部状态。
