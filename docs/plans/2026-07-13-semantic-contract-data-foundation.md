# Semantic Contract 数据基础层实施计划

## Goal

为 Semantic Layer V2 建立可版本化、可审计的语义契约持久化基础，使后续 Resolver 能从明确的业务定义中读取指标、维度和实体口径，而不修改现有分析编排与 SQL 安全链路。

## Scope

- 新增 `semantic_contracts` 数据库迁移，保存语义契约键、版本、类型、展示名称、业务定义、来源表字段、同义表达、默认过滤、时间粒度、聚合方式、状态与审计时间。
- 新增 Pydantic 读写契约和 PostgreSQL repository，支持按契约键读取启用版本、列出启用版本和创建新版本。
- 补充迁移声明、Pydantic 校验和 repository SQL 参数化的聚焦测试。

## Out of scope

- 不改动 `analysis_graph`、意图识别、Semantic Resolver、Prompt、SQL Guard 或 Executor。
- 不提供 API 路由、前端管理界面或预置业务语义数据。
- 不删除或改写既有 `metric_definitions`，两者在本阶段并存。

## Implementation steps

- [x] 定义最小可版本化表结构及唯一性、状态查询索引。
- [x] 实现 Pydantic 契约模型和 repository 的读取、列举、创建能力。
- [x] 编写数据层聚焦测试和迁移声明测试。
- [x] 应用真实 PostgreSQL migration，运行聚焦和后端全量测试，记录验证结果并补齐模块交付与 handoff。

## Validation plan

- `py -3 -m pytest backend/tests/test_semantic_contracts.py backend/tests/test_db_migrations.py`
- 条件允许时运行 `npm.cmd run backend:test`，由主线完成合并后的全量质量门禁。

## Risks

- PostgreSQL migration runner 会重复执行 SQL，因此迁移必须幂等。
- 契约版本首次只定义数据边界，后续 Resolver 接入前不能把它误当作 SQL 执行权限。
- 多 agent 同时修改 handoff，需只追加本模块事实，避免覆盖主线状态。
