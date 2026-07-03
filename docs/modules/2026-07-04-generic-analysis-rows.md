# 模块：数据问答通用 Rows 契约

当前状态：代码开发完成，验证已通过，随本次提交完成 commit 和 push，提交信息为 `实现数据问答通用Rows并通过验证`。

业务逻辑：

本模块让 `/api/analyze.rows` 返回 SQL Executor 的真实结果列，而不是固定包装成 `date/amount/orders/avg/refundRate`。业务分析人员看到的仍是简洁结果表，但系统可以适配更多查询列、换表场景和后续模型生成 SQL 的输出。

关键代码：

- `backend/app/schemas/analysis.py`：`AnalysisRow` 改为 `dict[str, string | int | float | bool | None]`。
- `backend/app/tools/analysis_presenter.py`：保留现有总结和指标卡计算用的内部 summary row，同时把响应 `rows` 改为 SQL 执行结果原始列。
- `frontend/src/types/analysis.ts`：`AnalysisRow` 改为 `Record<string, AnalysisValue>`。
- `frontend/src/pages/ChatPage.tsx`：结果表改为动态列渲染，支持常见列名中文化、金额/数量/百分比格式化和横向滚动。
- `backend/tests/test_api.py`：增加断言，确认销售趋势返回 `daily_sales` 而不是旧 `amount` 字段，城市客单价返回 `city_label` 和 `avg_order_value`。

数据契约：

`POST /api/analyze` 响应中的 `rows` 当前为：

```json
[
  {
    "order_date": "2026-06-01",
    "daily_sales": 1000.0,
    "order_count": 20,
    "avg_order_value": 50.0,
    "refund_rate": 0.0
  }
]
```

行值允许 `string`、`number`、`boolean` 和 `null`。前端不再依赖固定销售趋势字段。

验证：

- `npm run frontend:build`：已通过。
- `npm run backend:test`：73 passed，1 个 `StarletteDeprecationWarning`，不影响本模块。
- `npm run test:e2e`：已通过，question -> FastAPI -> AgentService -> Guard -> Executor -> result。

风险/后续：

- 前端聊天页当前最多展示前 6 列，避免普通用户页面过宽；后续可以增加列选择或完整表格弹窗。
- 自然语言总结仍主要面向 V1 已覆盖指标；模型生成更多类型 SQL 后，需要继续推进通用 Presenter。
- 本模块不新增固定 SQL 模板，后续应继续推进 schema/metric/memory 的混合检索能力。
