# 可执行 Query Plan 与失败诊断修复计划

## Goal

将“2017 年每月已支付订单销售额与订单数”这类多表问题的已确认业务口径，转为 SQL 模型和 Repair 可直接遵从的结构化约束；同时让管理员能诊断被拒绝的候选 SQL，并让前端失败提示反映真实原因。

## Scope

- 扩展 Query Plan，表达时间字段、分组表达式、规范过滤、关联策略、聚合粒度和技术输出别名。
- 将本次 Plan 专属合同传入 SQL 生成和 Repair Prompt，并保持 LLM 只生成、Guard/Executor 决定是否执行的边界。
- 在管理员运行详情中记录受限候选 SQL 诊断；普通会话响应、公共日志和评测摘要不暴露 Prompt、密钥或模型原始内容。
- 将前端 503 的通用“换一个更具体的问题”提示替换为安全、准确的 SQL 未满足业务口径提示。

## Out of scope

- 不添加固定业务 SQL 或绕过模型、Inspector、Guard、EXPLAIN 与只读 Executor。
- 不改变数据库业务数据、认证权限矩阵、模型供应商或并发模型。
- 不向普通用户展示候选 SQL、工具 Payload 或内部 Prompt。

## Implementation steps

- [x] 确认支付销售额按月问题的 QuerySpec、Semantic Contract 和当前 Prompt 数据缺口。
- [x] 扩展 Query Plan 和 Planner，生成可执行的时间、过滤、关联、粒度和别名约束。
- [x] 扩展 SQL 生成与 Repair Payload，使模型按本次合同生成并修复 SQL。
- [x] 仅向管理员运行详情加入候选 SQL 诊断，并保持列表接口与普通对话脱敏。
- [x] 修正前端 SQL 生成失败提示并同步 API 文档。
- [x] 增加 focused tests、前端构建和真实请求回归，记录结果。

## Validation plan

- Planner、SQL Generator、Inspector/Graph 和 Run Service focused pytest。
- 断言支付销售额按月计划包含真实时间列、支付谓词、去重关联策略和稳定别名；Repair Payload 包含同一合同。
- 验证管理员 `/api/runs/{run_id}` 可见候选 SQL，非管理员仍被拒绝。
- `npm.cmd run frontend:build` 与真实认证分析请求回归；评测工件仅保留本地。

## Risks

- 业务合同的执行约束若泛化过度，可能误约束其他多表问题；实现必须只在已确认指标和支付口径组合时启用。
- 候选 SQL 是内部调试信息，必须严格保持在已有管理员接口内。
- 云端模型仍可能不遵从合同；改动只能提升约束清晰度，不能承诺单次调用成功。
