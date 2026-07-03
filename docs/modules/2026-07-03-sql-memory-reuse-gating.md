# SQL Memory fast_path 表/意图约束完成说明

模块：SQL Memory fast_path 表/意图约束

当前状态：已完成实现、测试、标准问题评估和文档更新，等待提交并推送到 GitHub。

业务逻辑：

- 标准问题评估暴露出一个问题：部分用户、流量、优惠券问题会被 SQL Memory `fast_path` 复用到缺少关键业务表的历史 SQL。
- 本模块增加保守约束：当问题明显需要 `users`、`traffic_events`、`coupons`、`coupon_usages` 等关键表时，候选 SQL 必须包含这些表才能进入 `fast_path`。
- 如果候选得分很高但缺少关键表，不再直接复用为 `fast_path`，而是降级到 `rewrite_path`，让后续 SQL 生成链路重新处理。

关键代码：

- `backend/app/tools/sql_memory_tools.py`
  - 新增 `_required_tables_for_question()`，从中文问题中推断关键表。
  - 新增 `_sql_contains_required_tables()`，检查候选 SQL 是否包含关键表。
  - `retrieve_sql_memory()` 为候选写入 `required_table_match` 和 `required_tables`。
  - `plan_sql_reuse()` 要求高分且 `required_table_match=True` 才能进入 `fast_path`。
- `backend/app/schemas/memories.py`
  - `SqlMemoryCandidate` 新增 `required_table_match` 和 `required_tables`。
- `backend/tests/test_sql_memory_tools.py`
  - 覆盖缺少关键表时阻止 fast_path。
  - 覆盖关键表匹配时允许 fast_path。

数据契约：

- `SqlMemoryCandidate.required_table_match: bool`
- `SqlMemoryCandidate.required_tables: list[str]`
- `SqlReusePlan` 未变更。

验证：

- `npm run backend:test`：73 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`：20/20 链路执行成功，严格成功率 55%。
- 评估变化：
  - `memory_hit_rate` 从 100% 降到 60%。
  - `path_counts` 从全 fast_path 变为 `fast_path=12`、`rewrite_path=8`。
  - 说明错误记忆直接复用被部分拦截，剩余严格断言失败需要后续生成能力修复。

风险/后续：

- 关键词推断仍是启发式，只是先把明显错误的 fast_path 挡住。
- 严格成功率尚未提升，因为缺少关键表的问题降级到 rewrite 后，当前确定性生成仍无法覆盖所有用户、流量、优惠券语义。
- 下一步应把这些 rewrite/cold 问题交给模型 SQL Generator 或更强意图生成，并继续用评估集验证。
