# 数据分析 SSE 真实流式输出

## Goal

为数据分析会话新增 `POST /api/analyze/stream`，将真实 Agent 服务阶段和最终 `AnalyzeResponse` 以 SSE 发送给 ChatPage；前端可以取消正在进行的请求，同时保持会话只在服务实际完成后写入最终助手消息。

## Scope

- 新增流事件契约：`stage`、`result`、`error` 和 `done`。阶段只对应服务真正进入的处理节点，最终结果沿用完整 `AnalyzeResponse`。
- 为 `AgentService` 增加可选阶段回调，不重写 SQL Agent 的现有同步编排与安全边界。
- 新路由使用认证主体、同一请求 schema 和现有 `AgentService`；使用 SSE 响应与正确的 no-cache/no-buffer headers。
- 前端使用 `fetch`、`ReadableStream` 和 `AbortController` 消费 POST SSE，实时更新当前助手消息的真实阶段，接收 `result` 后渲染既有 SQL、图表和结果表。
- 用户点击取消时中断浏览器读取，不伪造完成消息；服务端已经开始的同步查询保持现有只读/超时保护。
- 补充 API 文档、focused SSE/服务测试和前端构建验证。

## Out of scope

- 不把最终 summary 拆分为模拟 `text_delta`，也不伪造打字效果。
- 不新增 WebSocket、后台任务队列、并发会话控制或 SQL 执行取消协议。
- 不修改 Semantic Contract、Query Plan、Inspector、Guard、Executor 或模型路由；只有既有数据分析链路可调用本接口。
- 不持久化中间阶段；会话持久化仍由成功/失败的 `AgentService._finish()` 统一处理。

## Implementation steps

- [x] 定义 SSE 事件编码与真实服务阶段回调，覆盖澄清、偏好、执行、完成和失败分支。
- [x] 新增认证保护的 `POST /api/analyze/stream`，以异步队列桥接同步 Agent 服务与 SSE 迭代器。
- [x] 新增前端 SSE parser/client，支持 result/error/done、网络错误和 AbortSignal。
- [x] 将 ChatPage 请求切换为真实流事件、阶段文案和取消控制；完成时复用当前结果渲染。
- [x] 更新 API/前端映射文档，增加 focused tests，并运行前端构建、SSE smoke 与 diff 检查。
- [x] 写模块记录、更新 handoff，独立 commit/push。

## Validation plan

- `pytest backend/tests/test_analysis_streaming.py backend/tests/test_conversation_service.py -q`，验证事件顺序、认证/错误映射和最终会话写入。
- 前端 stream parser unit tests（如本仓库现有工具链可运行）与 `npm.cmd run frontend:build`。
- 以 TestClient 或本地登录服务消费一次 SSE，确认 content type、stage/result/done 和无伪造 text delta。
- `git diff --check`，并扫描 ChatPage 不再调用同步 `analyzeQuestion()`。

## Risks

- 同步 Agent 运行在线程中完成后仍不能强制中止已开始的数据库查询；Abort 仅取消浏览器等待，Executor 的只读与超时边界不变。
- TestClient 可能缓冲 SSE 输出，因此 focused tests 以事件序列/内容为准，不把首字节时间作为通过条件。
- 现有服务没有 token 级对话模型输出。`text_delta` 必须等待 Dialogue Router 模块接入真实模型流后才能增加。
