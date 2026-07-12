# Authentication And Authorization Foundation

## Completed Behavior

- 新增独立的 `app_users`、`auth_sessions`、`auth_events` 表，以及 `query_runs.app_user_id` 所有者字段。认证不会复用 Olist 业务 `users` 表。
- 使用 `pwdlib[argon2]` 保存 Argon2id 密码哈希；随机不透明 session token 和 CSRF token 只保存 SHA-256 哈希。
- 提供注册、登录、注销、当前用户、密码修改、会话列表和指定会话撤销 API。会话以 HttpOnly、SameSite=Lax Cookie 传递；非 `GET` 请求会校验 `X-CSRF-Token`。
- 新增 `analyst/admin` 角色依赖。启用认证后，分析接口要求登录；指标写入、SQL Memory 和运行记录仅允许管理员。
- 前端登录、注册、登出、启动时恢复登录态和 `/app/*` 路由守卫已接入真实 API；统一 API Client 携带 Cookie 与 CSRF Header。
- 分析成功时会把认证主体写入 `query_runs.app_user_id`。本地 `AUTH_REQUIRED=false` 开发模式保持无主体记录，避免伪造一个数据库用户。

## Key Decisions

- `AUTH_REQUIRED=false` 只用于本地受控开发和既有测试兼容。`APP_ENV=production` 或 `prod` 时服务会拒绝关闭认证或关闭 Secure Cookie。
- 自助注册由 `AUTH_ALLOW_SELF_REGISTRATION` 显式控制；第一个注册用户不会自动成为管理员。
- CSRF Cookie 可由前端读取，session Cookie 不可由 JavaScript 读取。

## API And Data Contract

- 新增 `/api/auth/register`、`/api/auth/login`、`/api/auth/logout`、`/api/auth/me`、`/api/auth/password` 和 `/api/auth/sessions`。
- 启用认证后，未登录返回 `401`，角色不足或 CSRF 失败返回 `403`。
- `QueryRunRecord` 增加可空 `app_user_id`，保持历史运行记录兼容。
- 同步文档：`docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_error_auth.md`。

## Validation

```powershell
py -3 backend/scripts/init_db.py
.venv\Scripts\python -m pytest backend/tests/test_auth.py -q
.venv\Scripts\python -m pytest backend/tests/test_auth.py backend/tests/test_api.py backend/tests/test_runs.py -q
npm.cmd run backend:test
npm.cmd run frontend:build
```

- migration runner: `005_auth_and_user_ownership.sql` applied successfully.
- focused auth: `5 passed`.
- auth + API + runs: `17 passed`.
- backend suite: `202 passed, 1 warning` after the complete memory implementation.
- frontend build: passed.

## Remaining Risks And Follow-up

- 登录和注册限流需要 Redis 支撑；当前不以进程内计数器冒充生产级限流。
- 已实现当前用户撤销自身其他 session；管理员 session 管理和禁用用户待后续身份管理模块。
- 登录/注册限流优先使用 Redis；本地开发在 Redis 不可用时使用受限内存回退，生产环境会拒绝未受保护的认证请求。
- 会话和长期记忆的资源所有权将在 Phase 1/Phase 3 与数据模型一起实现。
- 并发、多线程、乐观锁、幂等重试、Redis 原子操作和后台归并均按用户要求延后。
