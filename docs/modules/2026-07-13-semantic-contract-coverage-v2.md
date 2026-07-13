# Semantic Contract Coverage V2

## Completed behavior

- 新增 migration `012_complex_semantic_contracts.sql`，以版本化、仅追加的方式登记订单时间范围、品类/商品排行、商品重量、运费、退款、评价、州/城市用户排行和晚送达订单等业务定义。
- 每条契约只保存来源表字段、聚合和声明性 Query Plan 形态，不保存可直接执行的 SQL。
- `QueryPlan` 现在会合并已解析契约的度量、维度、排序、限制、预期列和结果形态；未知概念仍不会被此层猜测或阻断。

## Key decisions

- 语义契约约束仅在 Resolver 已唯一匹配时生效，避免把词表变成开放式问题的硬限制。
- SQL 仍只能由模型生成，并必须继续通过 Inspector、Guard 和只读 Executor。

## API and data-contract impact

- 无公开 API 变更。
- 新增数据库语义资产；已在本地数据库执行 `init_db.py` 应用 migration。
- 内部 `question_intent.query_plan` 会包含来自契约的声明性形态信息。

## Validation

- `.venv\\Scripts\\python backend/scripts/init_db.py`：migration `012_complex_semantic_contracts.sql` 已成功应用。
- `.venv\\Scripts\\python -m pytest backend/tests/test_db_migrations.py backend/tests/test_query_planner.py backend/tests/test_semantic_resolver.py backend/tests/test_model_sql_generator.py`：`24 passed`。
- `npm.cmd run backend:test`：在 120 秒上限内未完成，未将其视为通过。
- `npm.cmd run eval:database-baseline -- --start 10 --limit 10 --report eval/reports/semantic_contract_v2_batch_002.json`：认证管理员评测，执行成功 `10/10`，严格成功 `7/10`，答案匹配 `7/10`。`database_011` 已正确获得订单时间范围；`database_017`、`018`、`020` 仍是分组语义失败。

## Remaining risks and follow-up

- 本地 `qwen2.5-coder:3b` 仍会在未覆盖的分组语义中生成错误聚合；下一步应新增订单/支付状态和支付方式金额等受审核契约，再由 benchmark 验证。
- 认证抽样不能替代完整 50-case 对照；后续跨模块合并后需重新运行完整集。
