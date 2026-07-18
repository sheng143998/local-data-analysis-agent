# 批量评测耗时与日志可观测性

## Goal

让长时间批量 SQL 评测逐 case 持久化 checkpoint，并在报告中提供 API 总耗时、Graph 节点耗时、最慢节点、模型调用路径和失败分类，以支持定位 Router、检索、模型、Repair、Guard、EXPLAIN、数据库执行和展示模块的性能瓶颈。

## Scope

- 为目标 SQL 评测加入逐 case 原子 checkpoint、控制台进度和显式 resume。
- 扩展评测报告，按 case 保留 API 总耗时、Graph 节点耗时、已知节点总耗时、未归因耗时、最慢节点、模型路由摘要、Repair 次数、Guard/EXPLAIN/Executor 状态。
- 增加批量聚合：各节点调用次数、平均值、p50、p95、最大值、总耗时和失败状态分布。
- 提供 focused 测试，确保中断后不会丢失已完成 case，恢复时不重复执行。

## Out of scope

- 不为提升速度引入并发或多线程；评测继续顺序执行。
- 不记录完整 Prompt、密钥、原始模型回复、SQL 结果行或用户敏感信息。
- 不改变 SQL 安全链路或业务 SQL 口径。

## Implementation steps

- [x] 定义报告耗时聚合与单 case 性能摘要。
- [x] 改造目标评测脚本的 checkpoint、控制台进度和 resume。
- [x] 补充评测 focused tests。
- [x] 使用替身 analyzer 验证耗时报告和既有单 case 报告兼容性。
- [x] 创建模块记录、更新 handoff、提交并推送。

## Validation plan

- `python -m pytest backend/tests/test_eval_runner.py -q`。
- 目标评测器使用替身 analyzer 运行小批，验证每条写 checkpoint、恢复时跳过已完成 case、输出阶段汇总。
- `git diff --check`。

## Risks

- API 总耗时包含 Router、鉴权、会话持久化和网络开销；未归因耗时必须明确标示，不伪造为某个 Graph 节点。
- checkpoint 文件属于本地评测工件，不提交；原子写入避免进程中断产生损坏 JSON。
