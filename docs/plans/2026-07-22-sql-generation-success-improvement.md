# SQL 生成成功率改进计划

## Goal

基于 `2026-07-19` 的 20 条结构化 SQL accuracy 基准，按失败类型提升 SQL 生成成功率和结构化行匹配率。优先解决模型生成/Repair 不稳定、检索上下文被误当作强制约束、SQL Memory 未命中三个问题；不以放宽安全边界或固定业务 SQL 换取成功率。

## Evidence baseline

基准报告：`eval/reports/sql_accuracy_20_checkpointed_baseline_20260719.json`。

| 指标 | 基线 |
| --- | ---: |
| 样本数 | 20 |
| SQL 生成/执行成功率 | 60%（12/20） |
| 严格成功率 | 35%（7/20） |
| 结构化行匹配率 | 40%（8/20） |
| SQL Memory 命中率 | 0% |
| SQL 生成平均耗时 | 22.89s |
| SQL 生成 p50 | 17.35s |
| API 平均耗时 | 57.32s |

已观察到的失败模式：

- 7 条请求返回 HTTP 503，主要发生在模型首次生成或一次 Repair 后未产生可执行 SQL，模型可用性和 Repair 长尾是首要问题。
- 品类、城市等样本已召回目标表和字段，但模型仍会漏表、漏排序/LIMIT、使用错误支付口径，或在 payments 一对多关联后重复累计订单金额；这不是单纯的召回缺失。
- 部分候选 SQL 被要求满足与问题无关的指标或表约束，例如品类排行被附加客单价、退款率等 token，导致安全但可执行的 SQL 被业务形态校验拦截。
- 高相似 SQL Memory 候选未形成 verified reuse，所有样本仍依赖模型生成或改写。
- 数据库执行平均约 0.26s，远低于模型生成和 Repair 耗时；本轮不以数据库执行计划优化作为主要成功率手段。

## Scope

- 将评测和运行 trace 的失败原因稳定归类为：模型无 SQL/超时、召回缺失、模型未遵循合同、业务校验误拦截、Guard/EXPLAIN/数据库执行失败、结果行不匹配。
- 明确 Query Plan、Semantic Contract 与 Retrieval Context 的优先级：只有已确认合同的表、过滤、聚合、排序和结果粒度可作为阻断条件；普通召回信息仅作为生成参考。
- 使 Inspector 的业务形态诊断支持一次定向 Repair 和可观测 warning，保留意图安全校验、SQL Guard、EXPLAIN 与只读 Executor 的阻断边界。
- 提升高频、结构化行已验证问题的 SQL Memory 写入质量和 verified reuse 覆盖，并验证参数化/时间条件变化不会造成错误复用。
- 针对支付去重、订单粒度、品类排行、城市排行和转化率补齐最小、可维护的指标定义、关联路径和 Repair 规则。

## Out of scope

- 不让 LLM 直接执行 SQL，不移除 SQL Guard、EXPLAIN、只读事务、超时、表字段白名单或资源上限。
- 不新增固定问题到固定 SQL 的主链路 fallback。
- 不以降低指标口径、跳过结构化行比较或仅提高 HTTP 200 比例作为成功。
- 不以 PostgreSQL 执行计划成本自动改写 SQL；执行计划观测可另立性能模块。

## Implementation steps

- [ ] 扩展 Eval/Run Trace 失败分类，并抽取 20 条基准逐例的首个失败节点、模型路径、Repair 结果、上下文覆盖与最终阻断原因。
- [ ] 复核 Query Planner：区分合同强制约束和检索参考项，修正无关 metric/table token 被升级为必需条件的规则。已完成 SQL Memory 子路径修复：普通召回指标不再阻断 verified reuse；生成/Repair 主路径仍待独立评测。
- [ ] 调整 Inspector/Graph：保留安全及确定性语义错误的阻断，对纯 SQL 形态建议执行一次定向 Repair，Repair 后以 warning 记录而非重复误拦截。
- [ ] 为高频问题补齐可信 SQL Memory 的写入、参数渲染和复用验证；重点覆盖时间范围、Top N 和支付状态变体。已完成 3 条真实冷/热对照：`3/3` 正确、`3/3` Memory 命中、平均总耗时降幅 `52.36%`；待扩大到 20 条集。
- [ ] 为五类高失败场景补充最小语义资产及回归用例：支付订单、品类排行、城市排行、流量转化和订单金额去重。
- [ ] 每次只改变一个变量，运行同一 20 条顺序评测并与本基线对比；无收益或准确率下降时回退该变量。已完成当前 Memory 修复后的 20 条验证：`19/20` 执行成功、`12/20` 行匹配、`5/20` fast path；后续每个失败归因改动仍须单变量复测。
- [ ] 完成 focused tests、标准评测、20 条结构化评测、模块记录、handoff、提交与推送。

## Validation plan

- focused pytest：Query Planner、SQL Inspector、Analysis Graph、SQL Memory、Eval Runner 和相关 Semantic Contract。
- `npm.cmd run eval:standard`，单列出模型无 SQL、Guard 拦截、EXPLAIN 失败、执行失败和结果不匹配数。
- 使用 `eval/datasets/sql_accuracy_20_sample.jsonl` 顺序执行，并写入独立报告和 checkpoint；不得覆盖当前基线。
- 以结构化行匹配为最终质量门槛，同时报告 execution/strict/row match、Memory 命中率、SQL generation/API 的平均与 p50/p95 延迟。
- `npm.cmd run frontend:build`、`git diff --check`。

## Acceptance criteria

- 相同 20 条样本的结构化行匹配率高于 40%，且不得低于基线执行成功率 60%。
- 每一条失败都能归入唯一的首要失败类别；不得以空 SQL、503 或未分类 warning 结束。
- 不出现因检索参考表/指标被误设为合同必需项导致的阻断回归。
- SQL Memory 对至少一组高频问题的等价变体完成 verified reuse，并通过表、指标、时间范围、Top N 与结果行验证。
- 安全回归保持：禁止写操作、未授权表字段、EXPLAIN 失败和只读执行失败均不得执行主查询。

## Risks

- 外部模型延迟和可用性会污染真实评测，因此报告必须把模型无 SQL/超时与 SQL 质量失败分开，不能将 503 误判为召回质量。
- 业务形态从阻断改为 warning 可能放行口径错误的 SQL；仅能在明确合同、结果行评测和管理员诊断完整保留的前提下推进。
- SQL Memory 复用阈值过低会扩大错误复用风险，必须继续使用当前 Query Plan/Inspector/Guard/EXPLAIN 全链路验证。
- 当前工作区已有未提交的分层校验改动；实施本计划时必须先确认其与本计划的重叠范围，避免覆盖或重复实现。
