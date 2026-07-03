# 数据问答通用 Rows 契约计划

## Goal

本模块把 `/api/analyze.rows` 从固定销售趋势字段推进为通用表格行结构，减少前端对 `date/amount/orders/avg/refundRate` 的硬编码依赖。后续换库、换表或模型生成不同列名时，普通用户仍能看到简洁结果表。

## Current task

当前正在做：验证已通过，准备提交并推送。

## Scope

包含：

- 后端 `AnalyzeResponse.rows` 改为 `list[dict[str, value]]`。
- Presenter 保留现有总结和指标卡逻辑，但 API `rows` 返回 SQL Executor 的真实列。
- 前端 `AnalysisRow` 改为通用记录类型。
- 聊天页结果表根据返回行动态生成列、中文化常见列名、格式化数字和百分比。
- 更新接口文档、前后端映射、README、handoff 和模块完成说明。
- 增加或调整测试，证明响应不再只依赖固定销售字段。

不包含：

- 不新增固定 SQL 模板。
- 不修改 SQL Generator / Rewriter 语义。
- 不新增开发者调试页。
- 不改变普通用户页面的模型、数据库状态、SQL Memory 分数隐藏原则。

## Module boundary

上游输入：

- SQL Executor 输出 `columns` 和 `rows`。
- Presenter 根据执行结果生成 `AnalyzeResponse`。

下游输出：

- `/api/analyze.rows` 返回通用 JSON 行。
- 前端聊天页动态渲染任意列的简单结果表。

预计触达文件：

- `backend/app/schemas/analysis.py`
- `backend/app/tools/analysis_presenter.py`
- `backend/tests/test_api.py`
- `frontend/src/types/analysis.ts`
- `frontend/src/pages/ChatPage.tsx`
- `docs/api.md`
- `docs/api_frontend_mapping.md`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-generic-analysis-rows.md`

## Business logic

业务分析人员提问后，不应该因为结果列不是“销售额/订单数/退款率”而看不到表格。系统应把真实 SQL 结果表以通用方式展示出来，同时继续保留自然语言分析、SQL、来源和可信说明。

## Data contract

`rows` 新契约：

```json
[
  {
    "order_date": "2026-06-01",
    "daily_sales": 1000.0,
    "order_count": 20,
    "avg_order_value": 50.0,
    "refund_rate": 0.2
  }
]
```

行值允许：

- `string`
- `number`
- `boolean`
- `null`

## Implementation steps

- [x] 读取 handoff、接口文档和现有 analyze 前后端代码。
- [x] 实现后端和前端通用 rows 契约。
- [x] 更新测试。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [~] commit 并 push。

## Validation plan

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`

本模块修改接口契约和前端展示，但不修改 SQL 语义生成，暂不强制运行 `npm run eval:standard`。

## Risks and open questions

- 前端动态列过多时需要横向滚动，本模块保留最多前 6 列展示，避免普通用户页面过宽。
- 后端总结仍基于当前 V1 业务指标做轻量归纳；后续模型 SQL 生成更多列后，Presenter 还需要更通用的总结策略。
