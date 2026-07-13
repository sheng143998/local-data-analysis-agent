# 订单支付状态语义契约覆盖完成记录

## 交付内容

- 新增 `backend/app/db/migrations/013_transaction_state_semantic_contracts.sql`，追加四个启用契约：
  - `order_status_distribution`：按 `orders.status` 统计订单数量。
  - `payment_status_distribution`：按 `payments.status` 统计支付记录数量。
  - `payment_method_record_count`：按 `payments.payment_type` 统计支付记录数。
  - `payment_method_paid_amount`：按支付方式汇总 `payments.amount`，并声明 `payments.status = 'paid'` 过滤。
- 契约只保存业务定义、来源字段和声明性 Query Plan，不包含可执行 SQL；重复执行使用 `ON CONFLICT (contract_key, version) DO NOTHING`，不覆盖历史口径。
- `Query Planner` 合并契约的声明性 `filters`，并把支付方式展示别名规范化为既有 `payment_type` 维度 ID，避免模型收到重复分组维度。
- 新增 Resolver、Planner 和 migration 内容回归测试，确认已知契约不会触发澄清，未知概念仍保持开放路径。

## 验证

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_semantic_resolver.py backend/tests/test_query_planner.py backend/tests/test_semantic_contracts.py backend/tests/test_db_migrations.py`：`18 passed`。
- `.venv\\Scripts\\python.exe backend/scripts/init_db.py`：真实 PostgreSQL 已成功应用 `013_transaction_state_semantic_contracts.sql`。
- 数据库核验：四个新增契约均为 `version=1, status=enabled`；实际解析四个标准问题均 `needs_clarification=false`，并生成预期实体、维度、支付过滤和 `grouped` 结果形态。
- `git diff --check`：通过；仅有 Git 的换行符提示，无空白错误。

## 约束与剩余风险

- 本模块没有写固定 SQL，也没有绕过模型、Inspector、Guard 或只读 Executor；契约过滤器仅作为 Query Plan 上下文传递。
- `payments` 可能一单多支付；本契约只汇总支付记录金额，不把 `orders.total_amount` 与支付记录直接 Join 汇总。
- 本模块未重新运行完整 authenticated 50-case；本地 `qwen2.5-coder:3b` 的空 SQL、错误 Join 和模型延迟仍需由主线完整评测确认。
