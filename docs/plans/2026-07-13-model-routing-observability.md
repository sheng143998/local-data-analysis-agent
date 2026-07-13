# Model Routing And Observability

## Goal

为意图、SQL、展示任务建立显式模型路由和安全可观测摘要，便于后续对本地 3B/7B/云端模型做 benchmark 驱动选择。

## Scope

- 新增任务角色到现有配置的确定性路由。
- 在运行日志中记录 provider/model/任务角色/延迟摘要，不记录密钥或完整 prompt。
- 覆盖意图与 SQL 路由选择测试。

## Out of scope

- 不自动下载模型、不将 schema/SQL 发送到未经批准的云端 SQL 模型。
- 不改变当前模型 endpoint 或安全边界。

## Implementation steps

- [ ] 定义 routing contract。
- [ ] 接入意图/SQL adapter 和 run trace。
- [ ] 测试、全量验证、文档、commit、push。

## Validation plan

- routing/model adapter/run logger focused pytest，后端全量。

## Risks

- 路由是基础设施，不代表模型质量提升；必须依赖 authenticated benchmark 做实际选择。
