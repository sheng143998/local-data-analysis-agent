# 空 SQL 的受控修复重试

## 完成行为

- 首次模型 SQL 为空且未通过意图校验时，Graph 进入一次 `repair_model_sql`，Repair Prompt 获得既有 Query Plan、验证错误和 Inspector 规则。
- 修复结果仍为空或不符合规则时，第二次校验将其标记为 `model_error` 并进入既有 Guard 失败路径。
- 图不会因空 SQL 重试无限循环，且没有新增固定 SQL 或跳过 Guard、EXPLAIN、只读 Executor。

## 验证

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_model_sql_generator.py -q`：`52 passed`。
- 已认证抽样：`eval/reports/empty_sql_repair_batch_001.json`，前 10 条执行 `4/10`、严格 `3/10`、答案 `3/10`，与修复前相同；六条空 SQL 均在唯一一次 Repair 后严格终止。
- `git diff --check`：通过。

## 质量结论和风险

- 重试逻辑覆盖了此前缺失的 Graph 分支，但当前本机 `qwen2.5-coder:3b` 在重试时仍返回无 `sql` 的响应，因此没有形成可量化提升。
- 该机制会使首次空 SQL 多一次模型调用；第二次必定终止。必须在稳定且获批准的 SQL 模型配置下重新运行全量 50-case，不能把当前抽样视为质量达标。

## 交付

- Commit：`dc53686`，已推送至 `origin/main`。
