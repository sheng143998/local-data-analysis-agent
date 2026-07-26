# 模块：SQL Memory 冷热链路评测

## Completed behavior

- `eval/scripts/run_eval.py` 新增 `build_memory_warmup_comparison()`，可将同一 case 集合的冷链路报告与已审核 SQL Memory 热链路报告逐条配对。
- 对比报告同时输出正确性保持情况、热链路 Memory 命中率、总回答耗时和 `sql_generation` 耗时的平均/p50/p95，以及相对降幅。
- 效率只针对“冷链路严格正确且热链路命中 verified SQL Memory”的同一 case 计算；样本不足或出现正确性回归时，报告明确不应宣称性能提升。
- CLI 增加 `--compare-cold-report` 与 `--compare-warm-report`。两个参数必须成对提供，输出写入 `--report`；该模式只读取报告，不改动 SQL Memory 的可信状态。
- SQL Memory 测试覆盖新成功 SQL 为 `executed`、不能进入 fast path；只有审核为 `verified` 后才可以命中 fast path。已有 Graph 继续保证命中后仍经当前校验、Guard、EXPLAIN 和只读 Executor。

## Usage

1. 使用同一数据集运行冷链路，结构化行正确的成功 SQL 会写入 Memory，但保持 `executed`。
2. 管理员只审核已验证正确的记录，将其提升为 `verified`。
3. 使用相同数据集运行热链路，另存报告。
4. 运行：

```powershell
.venv\Scripts\python.exe eval/scripts/run_eval.py `
  --compare-cold-report eval/reports/sql_memory_cold.json `
  --compare-warm-report eval/reports/sql_memory_warm.json `
  --report eval/reports/sql_memory_warmup_comparison.json
```

## Key decisions

- 不自动提升 `executed` 为 `verified`。数据库执行成功不等于业务口径已审核，自动提升会破坏 Trusted SQL Memory 的安全边界。
- 不只对比 HTTP 200 或 Memory 命中率；热链路必须保持结构化结果正确，才纳入效率比较。
- 不将冷/热报告中不同 case 混合比较，避免问题难度差异伪造性能收益。

## API and data-contract impact

- 无公开 API、数据库迁移或前端改动。
- 新增评测 JSON 的 `verified_sql_memory_warmup` 对比格式，仅作为本地评测工件。

## Validation

- `.venv\Scripts\python.exe -m pytest backend/tests/test_sql_memory_tools.py -q`：`13 passed`。
- `.venv\Scripts\python.exe -m pytest backend/tests/test_eval_runner.py -q -k "memory_warmup_comparison"`：`1 passed, 21 deselected, 1 warning`。
- `.venv\Scripts\python.exe -m compileall eval/scripts/run_eval.py`：通过。
- `git diff --check`：通过。
- 组合 focused suite 同时存在 4 个既有失败，均来自工作区已存在的分层 SQL 校验未提交改动与旧断言不一致；本模块未修改这些实现或测试。具体为两个 Eval strict 判定旧断言，以及两个 Graph 节点仍期望 `selected_sql` 回填的旧断言。

## Real smoke result

- 冷链路：`eval/datasets/sql_accuracy_smoke.jsonl` 的三条多表问题均执行成功、结构化行匹配，SQL 正确率为 `3/3`；全部为 `rewrite_path`，SQL Memory 命中 `0/3`，平均回答耗时 `29.08s`。
- 审核：只将上述三条已人工核对口径且结构化行正确的 `executed` Memory 提升为 `verified`。订单金额 SQL 使用已支付订单去重子查询，避免 payments 一对多关联重复累计。
- 热链路：相同三条仍为 `3/3` 执行成功和结构化行匹配，但 Memory 命中仍为 `0/3`，全部降级为 `rewrite_path`，平均回答耗时 `36.23s`。因此配对报告没有符合条件的热样本，不能计算或宣称延迟收益。
- 对比报告：`eval/reports/sql_memory_warmup_comparison_20260722.json`，其中 `eligible_case_count=3`、`warm_memory_hit_count=0`、`total_latency_reduction_pct=null`。
- 诊断：热测的候选相似度为 `0.9455-0.98`，但复用校验将召回的无关指标（如客单价、退款率）作为必需 token；时间谓词校验也未识别 `CAST('2017-01-01' AS DATE)` 与期望 `DATE '2017-01-01'` 的等价性，导致已验证 SQL 被降级。

## Fix and final result

- Memory 复用校验现在只使用已确认 QuerySpec 的必需指标；普通召回指标仍提供给生成/Repair，但不会阻断已审核 SQL。
- 时间边界校验识别 PostgreSQL `CAST('YYYY-MM-DD' AS DATE)`、`DATE 'YYYY-MM-DD'` 与普通日期字符串，仍要求开始和结束两个半开区间端点。
- 当候选集中同时存在 `executed` 和满足全部条件的 `verified` 记录时，复用规划器优先选择 verified 记录，避免新写入的未审核变体遮蔽可信 SQL。
- `verified` Memory 后续被模型路径再次成功写入时，只更新成功次数、平均耗时和最近使用时间；不会降级为 `executed`、覆盖审核过的 SQL 或覆盖其 schema/合同指纹。
- 最终热链路：三条均为 `fast_path`、`3/3` 执行成功和结构化行匹配，Memory 命中 `3/3`，平均回答耗时由冷链路 `29.08s` 降至 `13.86s`。
- 最终配对报告：`eval/reports/sql_memory_warmup_final_comparison_20260722.json`。三个可比较样本的总回答平均降幅为 `52.36%`；热链路没有 `sql_generation` 或 Repair 节点耗时。
- 回归：`.venv\Scripts\python.exe -m pytest backend/tests/test_memory_repository.py backend/tests/test_sql_memory_tools.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_eval_runner.py -q`：`75 passed, 1 warning`。

## Twenty-case validation

- 报告：`eval/reports/sql_accuracy_20_memory_current_20260722.json`；20 条按顺序完成并写入 checkpoint。
- 执行成功 `19/20`（`95%`），结构化行匹配和语义准确率均为 `12/20`（`60%`）。唯一未返回可执行 SQL 的 `speed_006` 是“2017 年成交额是多少？”，被模型误判为需要澄清。
- 当前 SQL Memory 命中 `5/20`（`25%`），五条均为 `fast_path` 且结构化行正确；未发生已命中 Memory 的结果回归。
- `fast_path` 平均回答耗时 `12.68s`；13 条 `rewrite_path` 平均 `24.99s`。该数值是不同问题复杂度下的路径分组观察，不能替代同一问题冷/热对照；同题 3 条对照仍是 `52.36%` 平均降幅的因果证据。
- 数据库执行平均 `0.28s`，SQL 生成在 14 条路径中平均 `8.23s`，Repair 在 3 条路径中平均 `8.52s`，下一主要瓶颈仍是模型生成/Repair 与未归因 API 时间。

## Remaining risks and follow-up

- 当前结论基于 3 条 smoke，下一步应扩大到相同 20 条结构化集，单列 Memory 未命中、结构化行回归和模型服务波动。
- 20 条验证已完成；下一步应针对 8 条结构化行不匹配和 `speed_006` 的错误澄清，按 Query Plan、语义资产、模型无 SQL/Repair 分类逐项修复。
- Memory 命中仍必须受 context fingerprint、表覆盖和 SQL 语义校验约束；修复误拦截时未放宽这些安全边界。
