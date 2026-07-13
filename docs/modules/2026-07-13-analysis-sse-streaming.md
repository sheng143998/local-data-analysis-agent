# 数据分析 SSE 真实流式输出

## Completed behavior

- 新增认证保护的 `POST /api/analyze/stream`。请求体与同步 `/api/analyze` 一致，服务以 `text/event-stream`、no-cache 和禁用代理缓冲的响应头发送事件。
- `AgentService.analyze()` 新增可选阶段回调。只有在服务实际进入加载会话、检查长期偏好、合并补充信息、理解问题、等待补充、执行受控数据分析或保存会话结果时才发送 `stage`。
- 流事件为 `stage`、`result`、`error`、`done`。最终 `result` 是完整 `AnalyzeResponse`；SQL 无法生成时发送受控 `error`，不暴露异常栈、SQL、prompt 或内部上下文。
- `ChatPage` 已从同步 `analyzeQuestion()` 改用 `fetch + ReadableStream` 的 POST SSE client。真实阶段更新当前助手消息；最终结果继续渲染 SQL、图表和结果表；取消按钮通过 `AbortController` 移除未完成助手消息。

## Key decisions

- 现有数据分析 Agent 没有 token 级模型输出，因此没有把最终摘要拆成 `text_delta`。这避免将视觉打字效果误报为模型流式能力。
- SSE 使用异步队列桥接现有同步服务。浏览器中止只结束 SSE 等待，不能强制终止已经开始的同步查询；Executor 的只读事务、Guard 和超时边界保持生效。
- 流中间阶段不写入会话。最终成功、澄清和服务失败仍使用 `AgentService._finish()` 保存同一套会话状态和助手摘要。

## API/data-contract impact

- 新增兼容接口 `POST /api/analyze/stream`，不修改同步 `/api/analyze` 契约。
- SSE 已建立后，业务运行失败以 `error` 再 `done` 表示，HTTP 状态保持 `200`；未登录和请求校验失败仍在建立前返回普通 `401` 或 `422`。
- 前端新增 `streamAnalyzeQuestion()`，现有 `analyzeQuestion()` 保留给其他同步调用方。
- 已同步 `docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_smoke_examples.md` 和 README。

## Validation

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_analysis_streaming.py backend/tests/test_conversation_service.py -q`：`15 passed, 1 warning`。覆盖事件顺序、result、error、鉴权以及既有会话回归。
- `npm.cmd run frontend:build`：通过。Vite 仍提示 ECharts 入口包约 1.57 MB，未阻断构建。
- SSE focused test 验证 `Content-Type`、no-cache、`stage -> result -> done`、`error -> done`，并确认没有 `text_delta`。
- `git diff --check`：通过。

## Remaining risks and follow-up

- 真实云端 Dialogue Router 接入后，只有能验证为模型 token 的输出才可以增加 `text_delta`；届时需补 token 顺序、断线和敏感数据脱敏测试。
- 浏览器取消不等价于数据库取消。高延迟查询的服务端取消需要在未来单独设计请求级取消标识和 Executor 协作，不能在本模块伪称已实现。
- 现有 `npm.cmd run test:e2e` 仍被本机 `AUTH_REQUIRED=true` 下的旧未登录 smoke 阻断，未在本模块绕过鉴权。

## Delivery

- 待本轮验证后独立 commit/push；不会包含本地评测工件。
