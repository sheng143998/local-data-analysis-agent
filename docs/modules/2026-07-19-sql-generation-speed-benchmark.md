# 模块：SQL 生成速度基准优化

## 结果

- 基准：三条多表 structure accuracy smoke 为 `3/3` strict/row match；SQL 生成平均 `21.1s`，API 平均 `42.4s`。
- 第一轮：合同优先裁剪 schema 与将输出上限设为 700。准确率保持 `3/3`，但 SQL 生成升至 `24.0s`、API 升至 `43.8s`，已回退。
- 第二轮：只将 SQL 模型响应契约从包含 `reasoning/tables/metrics` 的 JSON 缩为 `sql` 与可选 `warnings`。准确率保持 `3/3`、row match `100%`；SQL 生成降至 `19.0s`，约改善 `9.7%`；API 降至 `38.9s`，约改善 `8.3%`。该改动已保留。

## 关键决策

- 不裁剪模型必要的 schema/合同上下文，避免因上下文变化导致模型延迟和准确率波动。
- 删除后续链路不消费的模型输出字段，减少输出约束和响应负担；Parser 仍兼容历史响应中的可选字段。

## 验证

- `python -m pytest backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py -q`：`53 passed`。
- accuracy smoke：`3/3` strict 成功、结构化参考行匹配。
- 最终全量相关回归、前端构建与差异检查待提交前执行。

## 风险与后续

- 三条 smoke 只能证明方向正确；后续应以更大的带参考行数据集验证 p50/p95 与准确率。
- 当前最大剩余瓶颈仍是 SQL 模型调用本身，下一步优先增加意图模型耗时观测、Verified SQL Memory 命中率和分模型路由对比。

## 交付

- 实现提交：`762c53a`（`优化SQL生成响应速度`）。
- 推送：已推送至 `origin/main`。
