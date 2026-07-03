# SQL Guard 与只读执行说明

## 目标

任何生成或复用的 SQL 都不能直接执行，必须先经过 Validator 和 Guard，再交给只读 Executor。

## Validator

实现文件：

```text
backend/app/tools/sql_validation_tools.py
```

主要检查：

- SQL 非空。
- 只能单条语句。
- 只能 `SELECT`。
- 禁止 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`CREATE` 等写操作或 DDL。
- 禁止访问非白名单表。
- 禁止 `SELECT *`。
- 缺少 `LIMIT` 时给出 warning。

## Guard

`guard_sql()` 在 Validator 基础上输出 `SqlGuardResult`：

- `allowed`
- `final_sql`
- `errors`
- `warnings`

如果查询缺少 `LIMIT`，Guard 会自动补充默认最大行数。

## 允许表

默认白名单来自 `backend/app/schemas/sql_validation.py`：

- `users`
- `products`
- `orders`
- `order_items`
- `payments`
- `refunds`
- `reviews`
- `traffic_events`
- `coupons`
- `coupon_usages`
- `inventory_snapshots`
- `product_costs`

## Executor

实现文件：

```text
backend/app/tools/sql_execution_tools.py
```

只接受 Guard 放行后的 `final_sql`。返回：

- `success`
- `blocked`
- `error`

并标准化列名、行数据、行数和耗时。

## 当前验证

相关测试：

- `backend/tests/test_sql_validation_tools.py`
- `backend/tests/test_sql_execution_tools.py`
- `backend/tests/test_api.py`

标准命令：

```bash
npm run backend:test
npm run test:e2e
```

## 已知边界

- 表字段存在性目前主要依赖白名单和 SQL 解析，后续可结合 `schema_metadata` 做更严格字段校验。
- Guard 不判断业务语义正确性；语义质量通过评估集逐步增强。
