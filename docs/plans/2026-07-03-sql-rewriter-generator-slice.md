# SQL Rewriter / Generator 最小切片计划

## Goal

让 V1 标准问题“最近 90 天每月订单数是多少？”进入真实 `analyze` 链路，形成确定性 SQL Generator / Rewriter 的最小闭环。

## Current task

当前正在做：SQL Rewriter / Generator 最小切片已完成，等待提交推送。

## Scope

- 包含：解析按月粒度、识别订单数意图、生成月度 SQL、接入 `/api/analyze`、补充单元测试和 API 测试。
- 不包含：真实 LLM 调用、复杂 prompt、pgvector embedding、跨表复杂指标生成。

## Module boundary

- 上游输入：用户自然语言问题、SQL Memory reuse plan、schema/metric retrieval context。
- 下游输出：Guard 可校验的 PostgreSQL SELECT SQL、标准 `AnalyzeResponse`。
- 主要文件：`sql_template_tools.py`、`sql_generation_tools.py`、`analysis_graph.py`、测试与文档。

## Business logic

业务分析人员可以直接询问“最近 90 天每月订单数是多少？”。系统无需用户懂 SQL，会自动识别时间范围、按月粒度和订单数指标，执行只读查询并返回结论、SQL、结果表和可信来源。

## Data contract

- `SalesTrendParameters`: 新增 `metric`，支持 `sales_amount` / `order_count`。
- `GeneratedSql`: 输出生成路径、SQL、参数和提示。
- `/api/analyze`: 仍返回既有 `AnalyzeResponse`，不破坏前端契约。

## Implementation steps

任务清单：
- [x] 扩展 SQL 模板参数解析。
- [x] 新增确定性 SQL Generator / Rewriter 工具。
- [x] 接入 analyze graph。
- [x] 补充单元测试和 API 测试。
- [x] 跑完整验证。
- [x] 更新模块文档、README、handoff。

## Validation plan

- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and open questions

- 当前“最近 90 天每月”仍按最近 3 个有交易月份表达，不是严格自然日窗口。
- Rewriter 是确定性最小切片，尚未接入真实 LLM。
