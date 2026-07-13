# 安全 Dialogue Router 与通用聊天

## Completed behavior

- 新增 `general_chat`、`data_analysis`、`clarification`、`explain_result`、`unsupported` 分流；默认不访问数据库。
- 只有明确数据问题进入既有 SQL Agent；通用聊天、结果解释和越权请求在 Graph 前完成。
- 新增独立 `DIALOGUE_MODEL_*` 配置。模型仅接收有限会话文本/摘要，不接收 schema、SQL、rows、密钥或运行追踪；未配置或失败时诚实降级。

## Validation

- `pytest backend/tests/test_dialogue_router.py backend/tests/test_analysis_streaming.py -q`：`6 passed, 1 warning`。
- `npm.cmd run frontend:build` 与 `git diff --check`：通过。

## Delivery

- 待本轮 commit/push；未包含评测工件。
