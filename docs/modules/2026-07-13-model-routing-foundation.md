# Model Routing Foundation

## Completed behavior

- 新增任务角色到 provider/model/base URL 的集中路由。
- 意图解析已使用 `intent` 路由，SQL 生成/修复角色已具备可调用路由契约。
- 路由不输出密钥、完整 prompt 或用户数据。

## Validation

- routing/intent/model adapter focused `22 passed`。

## Remaining risks

- SQL Adapter 与 run trace 的 provider/model/latency 摘要尚待接入。
- 路由基础不代表模型质量提升，必须用 authenticated benchmark 比较模型。
