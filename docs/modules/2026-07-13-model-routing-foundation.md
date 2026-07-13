# Model Routing Foundation

## Completed behavior

- 新增任务角色到 provider/model/base URL 的集中路由。
- 意图解析已使用 `intent` 路由，SQL 生成/修复角色已具备可调用路由契约。
- SQL generator 已使用 `sql_generation` / `sql_repair` 路由；run trace 新增安全的 provider/model/latency 摘要。
- 路由不输出密钥、完整 prompt 或用户数据。

## Validation

- routing/intent/model adapter focused `22 passed`。
- SQL generator/run trace/routing 回归 `17 passed, 1 warning`。

## Remaining risks

- 路由基础不代表模型质量提升，必须用 authenticated benchmark 比较模型。
