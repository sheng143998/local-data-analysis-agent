# 模块：SQL 准确率与路由延迟优化

## 已完成行为

- `EvalCase` 支持 `expected_rows`。评测现在按顺序比较参考行中的指定字段，结果写入 `row_match`、`row_match_rate` 与 `semantic_accuracy_rate`，不会只依赖文本 token。
- 新增 `eval/datasets/sql_accuracy_smoke.jsonl`，覆盖已支付订单数、已支付订单金额和品类订单商品数/销售额排行三条多表问题。
- 明确数据请求由 Dialogue Router 确定性进入 `data_analysis`，不再调用 Router 模型；普通聊天、结果解释、待澄清和越权拒绝边界不变。

## 真实结果与性能

- 结构化 SQL accuracy smoke：`3/3` 执行成功、严格成功、参考行匹配。
- 端到端平均 `42.4s`；Graph 已知节点平均 `26.9s`。
- SQL 生成平均 `21.1s`，上下文检索平均 `2.8s`，数据库执行平均 `0.18s`。数据库不是当前性能瓶颈。
- Router 快速路径通过替身回归证明不调用 Router 模型；意图模型耗时尚未纳入 Graph 节点明细，是 API 未归因时间的一部分。

## 验证

- `python -m pytest backend/tests/test_eval_runner.py backend/tests/test_dialogue_router.py -q`：`28 passed, 1 warning`。
- `python eval/scripts/run_eval.py --dataset eval/datasets/sql_accuracy_smoke.jsonl --report eval/reports/sql_accuracy_smoke_20260719.json`：`3/3` execution/strict/row match 通过。
- 前端构建与差异检查待最终提交前执行。

## 后续优化优先级

1. 为意图解析增加节点耗时记录，分离 Router 已消除耗时与 Intent 模型耗时。
2. 为稳定高频问题提升 SQL Memory 的 verified reuse 覆盖，避免每次重新生成 SQL。
3. 缩减 SQL Generator 的检索上下文和输出 token 上限，并在模型服务侧选择更低延迟的 SQL 模型；不得以固定 SQL 绕过合同链路。

## 交付

- 实现提交：`31b1243`（`提升SQL准确率评测与路由速度`）。
- 推送：已推送至 `origin/main`。
