# 合同 SQL 强制校验

## Completed behavior

- Query Plan 现在携带已审核 Semantic Contract 的来源表、来源字段和聚合方式。
- SQL Generator 明确收到合同约束；模型只能在该合同、Query Plan 和召回 schema 范围内生成 SQL。
- SQL Inspector 使用 AST 校验合同来源字段、聚合、计划过滤、最终输出列、排序方向和精确 Top N Limit。
- 不符合合同的 SQL 在 Guard 和 Executor 前进入有限 Repair；二次失败会停止为 `model_error`，不再写死订单数 SQL。
- 新增目标评测脚本，自动选择历史 50 Case 严格失败项和固定随机 5 条对照项。

## Validation

- `python -m pytest backend/tests/test_sql_inspector.py backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_query_planner.py -q`：`61 passed`。
- `python -m compileall -q backend/app`：通过。
- `git diff --check`：通过。
- 首次 29 条真实目标评测报告：`eval/reports/targeted_contract_eval_20260718.json`。执行 `11/29`、严格 `3/29`、答案 `4/28`，17 条受云端 503 影响，不能作为模型质量横向结论。
- 第二次 29 条重测达到 30 分钟进程上限且报告未落盘。原因是评测器仅在全部 case 完成后写报告，未实现逐条 checkpoint；该问题已记录为后续性能专项。

## Remaining risks

- 现有 Semantic Contract 尚未完整覆盖库存、成本、复购和统一格式化口径；缺失合同应拒绝或澄清，不能期待模型猜对。
- 当前 SQL 真实评测存在云端模型长尾和 503，必须将服务错误与业务语义错误分开统计。
- 目标评测器需要增加逐条 checkpoint、耗时阶段输出和恢复能力，避免长任务超时丢失结果。

## Delivery

- 评测 JSON 均为本地工件，不提交；本模块代码、测试、计划和 handoff 将随本次提交推送。
