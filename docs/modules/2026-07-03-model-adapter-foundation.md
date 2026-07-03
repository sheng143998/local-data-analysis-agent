# 统一 ModelAdapter 基础层完成说明

模块：统一 ModelAdapter 基础层

当前状态：已完成实现、测试和文档更新，等待提交并推送到 GitHub。

业务逻辑：

- 后续 SQL Generator / Rewriter 需要调用外部或本地模型时，统一通过 ModelAdapter，不允许在 Agent 节点、工具函数或服务里直接调用 SDK 或 HTTP。
- ModelAdapter 支持 OpenAI-compatible `chat/completions` 请求结构，可配置 provider、base URL、model、timeout 和 retry。
- 普通用户界面不展示模型 provider、连接状态、密钥、原始 prompt 或 raw response。
- 真实 API key 只从本机 `backend/.env` 读取，`.env.example` 只保留占位值。

关键代码：

- `backend/app/core/config.py`
  - 新增 `MODEL_PROVIDER`、`MODEL_BASE_URL`、`MODEL_NAME`、`MODEL_API_KEY`、`MODEL_TIMEOUT_SECONDS`、`MODEL_MAX_RETRIES` 配置读取。
- `backend/app/core/model_adapter.py`
  - 新增 `ModelMessage`、`ModelRequest`、`ModelUsage`、`ModelResponse`、`ModelAdapterConfig`。
  - 新增 `ModelAdapter.chat()`，负责构造 OpenAI-compatible payload、header、timeout、retry 和结构化错误。
  - 新增可注入 `ChatTransport`，单元测试可用 fake transport，不依赖真实模型服务。
- `backend/tests/test_model_adapter.py`
  - 覆盖 payload、Authorization header、空 messages、HTTP retry 和 transport error。

数据契约：

- 输入：`ModelRequest.messages`、`temperature`、`max_tokens`、`response_format`、`trace_id`。
- 输出：`ModelResponse.ok`、`content`、`provider`、`model`、`latency_ms`、`usage`、`error_code`、`error_message`。
- 错误：空消息、HTTP 错误和 transport 异常都转为结构化响应，不向调用方抛裸异常。

验证：

- `npm run backend:test`：59 passed，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 本模块只完成模型调用基础层，`/api/analyze` 尚未启用真实模型 SQL 生成。
- 后续需要把 SQL Generator 接到 ModelAdapter，并把模型调用摘要写入 `tool_calls`，但普通用户仍不展示调试细节。
- embedding adapter 尚未实现。
