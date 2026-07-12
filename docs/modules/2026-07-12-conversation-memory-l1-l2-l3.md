# Conversation Memory L1 L2 L3

## Completed Behavior

- `POST /api/analyze` 现在支持可选 `conversation_id`。新问题创建会话，后续问题使用同一 ID；响应返回会话 ID、待澄清标识和状态。
- L2 会话状态在每个用户/助手可见轮次写穿。生产配置使用 Redis JSON 会话键和 owner ZSET 索引，单个会话和索引的 TTL 均为 72 小时；本地 Redis 不可用时仅在非生产环境回退至进程内存。
- 会话状态包含 `PendingClarification` 和 `current_analysis`。Follow-up Resolver 通过确定性合并已保存的 QuerySpec 槽位，支持补答、另起问题和取消，不生成用户回复、不执行 SQL。
- L1 使用可替换的保守 token 估算器，默认 8000 token 输入预算、1000 token 输出预留、60% 轻量和 80% 激进水位。压缩只生成结构化滚动摘要，原始 L2 会话仍按 TTL 保存。
- L3 新增 `memory_subjects`、`long_term_memories`、`long_term_memory_events`。仅从用户明确“记住/默认/忘记”命令保存货币和默认粒度偏好；冲突会 supersede 旧版本，忘记会 revoke。
- L3 active 偏好只进入意图解析上下文，不进入 SQL 生成器、Guard 或只读 Executor。用户可在个人中心查看并删除偏好。

## Security And Ownership

- 会话和长期偏好都按认证主体所有权过滤；跨主体读取或续写会话返回 `404`。
- 开发模式的固定主体使用 `owner_id=None`，仅用于本地兼容，不能作为生产多用户隔离方案。
- 完整 SQL、完整 rows、工具 payload 和普通聊天不会写入 L3；L2 助手消息仅保存结果摘要和指标预览。

## API Contract

- `POST /api/analyze`: 请求新增可选 `conversation_id`，响应新增 `conversation_id`、`pending_clarification`、`conversation_status`。
- `GET /api/conversations`、`GET /api/conversations/{conversation_id}`: 会话列表和消息恢复。
- `GET /api/user-memories`、`DELETE /api/user-memories/{memory_key}`: 当前用户的长期偏好控制。
- 已同步 `docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_error_auth.md`。

## Validation

```powershell
py -3 backend/scripts/init_db.py
.venv\Scripts\python -m pytest backend/tests/test_conversation_service.py -q
.venv\Scripts\python -m pytest backend/tests/test_long_term_memory_service.py backend/tests/test_conversation_service.py backend/tests/test_working_memory.py -q
npm.cmd run backend:test
npm.cmd run frontend:build
npm.cmd run eval:standard
```

- migration runner: `006_long_term_memories.sql` applied successfully.
- conversation API continuation: passed; covers vague question, “销售额，2017年” follow-up and recovered message history.
- L1/L2/L3 focused tests: `9 passed, 1 warning`.
- backend suite: `202 passed, 1 warning`.
- frontend build: passed.
- Redis runtime verification: Docker Desktop started, `local-data-agent-redis` returned `PONG`, and a `RedisConversationStore` save/get round trip succeeded against `127.0.0.1:6379`.
- standard eval: process timed out after 304 seconds. It refreshed `eval/reports/latest_eval_report.json` before timeout with 20 cases (`12/20` execution success, `11/20` strict success), but the command exit was `124`; evaluation completion/reliability remains unresolved.

## Deferred Work And Risks

- 本地 Redis 容器已启动并验证可用；生产环境仍需要将 `REDIS_URL` 接入受管 Redis、持久化和健康检查，而非依赖本地 Docker 容器。
- No concurrency, multi-threading, optimistic locking, `client_turn_id` idempotency, Redis atomic operations or background consolidation were implemented, per scope.
- L3 uses a strict explicit-preference allowlist. Embedding/hybrid ranking for a larger preference taxonomy is deferred; active preferences are currently metadata-filtered.
- Login/register rate limiting, administration of other sessions and production Redis health/deployment automation remain separate follow-up work.
