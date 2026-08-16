# 查询加速/缓存、飞书集成、鉴权与数据隔离实施计划

> 状态：待实施。本计划覆盖查询结果缓存、并发控制、飞书机器人集成、鉴权登录增强和数据隔离。不涉及多数据源接入。

## Goal

在不引入多数据源、不改变 SQL Guard / EXPLAIN / 只读执行安全边界的前提下，完成：

1. 查询结果缓存与查询加速，降低重复问题延迟。
2. 适配 20-90 人小公司的单实例并发控制。
3. 飞书机器人对话取数，并支持通过飞书身份绑定本地用户。
4. 完善鉴权登录（飞书 SSO 绑定、角色扩展、接口强制鉴权）。
5. 完善数据隔离（会话/运行记录/SQL Memory/指标可见性按用户与角色隔离，并补充审计）。

## Scope

### 查询加速与结果缓存
- 新增 Redis 结果缓存，Redis 不可用时降级为进程内 LRU。
- 缓存 Key 包含 SQL、Query Plan、用户权限范围、schema/contract 版本。
- 缓存接入 Guard 后、EXPLAIN 前；命中时跳过 EXPLAIN 和数据库执行。
- 只缓存成功结果，不缓存 Guard 拒绝、EXPLAIN 失败、执行错误。
- 提供缓存清理 API（管理员）与缓存命中可观测字段。
- 保留 SQL Memory fast path 现有行为。

### 并发控制
- 新增全局分析并发限制、单用户并发限制、模型调用并发限制。
- 超限返回 HTTP 429，而不是排队打爆模型/数据库。
- DB 连接池增加 acquire timeout 与 overflow。
- `/api/health` 暴露 in-flight 与排队信息。

### 飞书集成
- 飞书机器人接收 `im.message.receive_v1` 事件。
- 支持 URL 验证、签名/Token 校验、Encrypt Key 解密。
- 飞书用户通过邮箱/union_id 绑定本地用户。
- 收到消息后立即 ACK，分析完成后异步发送结果。
- 结果以文本/卡片返回，包含摘要、指标、表格、SQL 来源（可配置）。
- 支持私聊和群聊 @机器人。
- 飞书侧普通用户不能修改指标；管理员可通过受控命令查看指标（修改命令后续再做）。

### 鉴权与数据隔离
- 角色扩展为 `admin / analyst / viewer`。
- 所有 `/api/*` 读接口也强制登录，不再裸奔。
- 会话、Run Trace、SQL Memory、长期记忆按 owner 隔离；admin 可查看全部。
- 指标增加可见范围 `public / team / private`，并按角色/owner 过滤。
- 指标修改记录审计（谁、何时、改了什么）。
- 飞书 SSO 登录：支持飞书扫码/免登登录 Web，绑定本地账号。

## Out Of Scope

- 多数据源接入。
- 业务数据行级权限（如“销售只能看华东”），但设计上预留 permission_hash。
- MFA / 短信验证码。
- 飞书定时推送、主动预警、订阅报表。
- 飞书内直接编辑指标（仅预留 admin 命令）。
- 多实例部署、K8s、微服务化。
- 深度分析 Agent 能力。

## Implementation Steps

### Phase 0：基线确认
- [x] 阅读 `docs/handoff/current.md`，确认当前未提交改动边界。
- [x] 运行 `git status`，记录工作区现状。
- [x] 确认现有后端测试与前端构建基线可运行（后端测试存在本地模型 503 环境问题）。
- [x] 更新 handoff 记录本计划路径、范围、风险和验证方式。

### Phase 1：查询结果缓存与查询加速
- [x] 在 `backend/app/core/config.py` 增加缓存与并发配置：
  - `QUERY_CACHE_ENABLED`
  - `QUERY_CACHE_TTL_SECONDS`
  - `QUERY_CACHE_MAX_ENTRIES`
  - `QUERY_CACHE_PREFIX`
  - `QUERY_CACHE_SCHEMA_VERSION`
- [x] 新建 `backend/app/services/cache_service.py`：
  - Redis 实现 + 进程内 LRU fallback。
  - `get` / `set` / `delete_prefix` / `clear_all`。
- [x] 新建 `backend/app/services/cache_key_builder.py`：
  - 输入：`schema_version`、`permission_hash`（当前为用户 ID）、`contract_version`、`query_plan`、`final_sql`。
  - 输出稳定字符串 Key。
- [x] 在 `analysis_graph.py` 中接入缓存：
  - Guard 通过后查缓存。
  - 命中：直接构造 `SqlExecutionResult`，标记 `cache_hit=true`。
  - 未命中：正常 EXPLAIN + 执行，成功后写缓存。
- [x] 缓存失效：
  - Schema/Context Refresh 后清空缓存。
  - 指标变更后清空缓存。
  - 管理员 `POST /api/cache/clear`。
- [x] Run Trace / `tool_calls` 增加 `cache_hit` 字段；`cache_source` / `cache_latency_ms` 留待可观测性阶段补充。
- [x] 新增缓存相关单测与集成测试。

### Phase 2：并发控制
- [ ] 在 `backend/app/core/concurrency.py` 新建并发限制器：
  - 全局分析信号量。
  - 每用户分析信号量（带清理）。
  - 模型调用信号量。
- [ ] 在 `AgentService.analyze()` 入口获取全局 + 用户信号量，超时返回 429。
- [ ] 在 `model_adapter.py` / `model_sql_generator.py` 包一层模型并发信号量。
- [ ] 增强 `backend/app/db/connection.py`：
  - 支持 `DB_POOL_ACQUIRE_TIMEOUT_SECONDS`。
  - 支持 `DB_POOL_MAX_OVERFLOW`。
- [ ] `/api/health` 暴露当前 in-flight、排队数、模型并发占用。
- [ ] 新增并发单测与并发集成测试。

### Phase 3：鉴权与数据隔离
- [ ] Migration `018_auth_roles_and_feishu.sql`：
  - 修改 `app_users.role` 检查约束，允许 `viewer`。
  - 新增 `feishu_bindings` 表。
- [ ] 更新 `backend/app/schemas/auth.py`：
  - `Role = Literal["admin", "analyst", "viewer"]`。
  - 增加飞书绑定相关 schema。
- [ ] 新增/调整用户管理 API（admin）：
  - 创建用户、禁用用户、修改角色。
- [ ] 所有 API 读接口强制鉴权：
  - `/api/metrics` 列表/详情。
  - `/api/runs`、`/api/memories`、`/api/long-term-memories`。
- [ ] 数据隔离：
  - Run Trace / SQL Memory / 长期记忆按 owner 过滤；admin 可看全部。
  - 指标增加 `visibility` 字段（`public / team / private`），非 admin 只能看到有权限的指标。
- [ ] 审计：
  - 指标创建/修改/删除记录 `auth_events` 或新 `audit_logs`。
  - 飞书登录/绑定操作记录审计。
- [ ] 更新前端类型与页面：
  - 角色展示支持 viewer。
  - MetricsPage 显示可见范围。
  - 新增用户管理页面（admin）。
- [ ] 新增鉴权/隔离相关测试。

### Phase 4：飞书集成
- [ ] 在 `backend/app/core/config.py` 增加飞书配置：
  - `FEISHU_ENABLED`
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_VERIFICATION_TOKEN`
  - `FEISHU_ENCRYPT_KEY`
  - `FEISHU_WEBHOOK_PATH`
- [ ] 新建 `backend/app/services/feishu_service.py`：
  - 获取 tenant_access_token（Redis 缓存）。
  - URL 验证、签名校验、事件解密。
  - 发送文本消息、发送卡片消息。
  - 解析消息事件。
- [ ] 新建 `backend/app/api/feishu.py`：
  - `GET /api/feishu/webhook` URL 验证。
  - `POST /api/feishu/webhook` 接收事件。
- [ ] 飞书用户绑定：
  - 根据飞书邮箱/union_id 自动匹配本地用户。
  - 未绑定用户回复引导绑定。
- [ ] 异步分析：
  - Webhook 立即 ACK。
  - 后台线程池执行 `AgentService.analyze`。
  - 完成后调用飞书 API 发送结果。
- [ ] 消息映射：
  - 摘要 → 文本。
  - 指标卡 → Markdown/卡片。
  - 表格 → 卡片表格。
  - SQL → 默认不展示，可配置。
- [ ] 飞书 SSO 登录：
  - 新增 `/api/auth/feishu/authorize` 与 `/api/auth/feishu/callback`。
  - 用飞书身份创建/绑定本地用户并建立本地 Session。
- [ ] 飞书侧限流与安全：
  - 事件去重。
  - 每个 open_id 限流。
  - 日志不记录密钥、完整消息。
- [ ] 新增飞书服务单测与 Webhook 集成测试。

### Phase 5：回归与收尾
- [ ] 运行 `npm run backend:test`。
- [ ] 运行 `npm run eval:standard`。
- [ ] 运行 `npm run frontend:build`。
- [ ] 运行 `npm run test:e2e` 或说明受阻原因。
- [ ] 检查 `git diff --check`。
- [ ] 按模块拆分 commit 并推送。
- [ ] 编写 `docs/modules/` 完成记录并更新 handoff。

## Validation Plan

| 变更 | 最低验证 |
| --- | --- |
| 缓存服务 | 单测 + 同一问题连续两次第二次命中缓存且不执行 DB |
| 并发限制 | 并发单测 + 慢速 mock 下多余请求返回 429 |
| 鉴权/隔离 | API 测试：未登录 401、非 owner 404/403、admin 可看全部 |
| 飞书 Webhook | 单测 URL 验证/解密/解析 + 手动真实飞书消息 |
| 飞书 SSO | 单测回调换 token + 手动扫码登录 |
| 前端 | `npm run frontend:build` |
| 回归 | 标准 eval 与后端测试 |

## Risks

- 缓存可能让不同权限用户读到越权数据：必须把 permission_hash 放入 Key。
- 缓存失效不完整会导致脏数据：schema/contract 变更后必须清前缀。
- 并发限制可能把模型超时变成用户 429：需要合理超时与错误文案。
- 飞书异步回复可能丢失任务：需要任务状态记录和失败重试策略。
- 飞书 SSO 与本地密码登录并存会带来账号绑定复杂度：先以邮箱匹配为主。
- 指标可见性改动会影响现有前端与评测：需要同步更新类型和测试。
- 工作区已有未提交改动：实施前先确认边界，避免覆盖用户修改。

## Review Questions

1. 飞书第一版是否只做“对话取数 + 身份绑定”，不做飞书内指标管理？
2. 是否接受 `viewer` 角色只能看结果、不能看 SQL 详情？
3. 指标可见范围第一版是否只做 `public / private`，`team` 延后？
4. 缓存 TTL 默认值建议 `300s`，是否可以？
5. 并发上限建议全局 8、单用户 2、模型 2（本地）/ 4-8（云端），是否可接受？
