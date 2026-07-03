# 退款率 / 支付成功率查询切片计划

## Goal

让 V1 标准问题“哪个商品品类退款率最高？”和“每个支付方式的成功率是多少？”进入真实 `analyze` 链路，补齐复杂指标查询的最小闭环。

## Current task

当前正在做：退款率 / 支付成功率查询切片已完成，等待提交推送。

## Scope

- 包含：识别退款率、支付成功率、支付失败率问题，生成只读聚合 SQL，复用 Guard / Executor / Presenter / Memory 链路。
- 包含：补充单元测试、API 测试、README、模块文档和 handoff。
- 不包含：真实 LLM SQL Generator、动态前端列配置、严格自然日过滤。

## Module boundary

- 上游输入：用户问题、SQL Memory reuse plan、schema/metric retrieval context。
- 下游输出：兼容现有 `AnalyzeResponse` 的中文结论、SQL、结果表、来源和可信说明。
- 主要文件：`sql_template_tools.py`、`schema_retriever.py`、`analysis_presenter.py`、测试与文档。

## Business logic

业务分析人员可以直接问退款率最高的品类或每种支付方式的成功率。系统自动选择指标口径和聚合维度，执行只读 SQL，并返回业务可读结论。

## Data contract

- `SalesTrendParameters.metric` 扩展为 `category_refund_rate` / `payment_success_rate` / `payment_failure_rate`。
- `AnalyzeResponse.rows[].date` 在复杂指标问题中承载品类或支付方式名称。
- `AnalyzeResponse.rows[].refundRate` 在退款率问题中表示退款率，在支付问题中表示成功率或失败率。

## Implementation steps

任务清单：
- [x] 扩展参数解析和 SQL 渲染。
- [x] 接入 schema 召回和结果展示。
- [x] 补充测试。
- [x] 更新 README、模块文档、handoff。
- [x] 跑完整验证、提交并推送。

## Validation plan

- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and open questions

- V1 先使用订单是否存在退款记录计算退款率，后续可细化为退款金额口径。
- 支付成功率基于 `payments.status = 'paid'`，后续可结合真实支付失败状态扩展。
