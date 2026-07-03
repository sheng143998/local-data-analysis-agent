# 毛利率查询切片计划

## Goal

让 V1 标准问题“最近 30 天毛利率最高的商品品类是什么？”进入真实 `analyze` 链路，继续覆盖多表复杂经营指标。

## Current task

当前正在做：毛利率查询切片已完成，等待提交推送。

## Scope

- 包含：识别毛利率问题，生成品类维度毛利率 SQL，使用 `order_items`、`products`、`product_costs`、`payments`。
- 包含：补充单元测试、API 测试、README、模块文档和 handoff。
- 不包含：严格自然日窗口、动态前端列配置、真实 LLM SQL Generator。

## Module boundary

- 上游输入：用户自然语言问题、SQL Memory reuse plan、schema/metric retrieval context。
- 下游输出：兼容现有 `AnalyzeResponse` 的中文结论、SQL、结果表、来源和可信说明。
- 主要文件：`sql_template_tools.py`、`schema_retriever.py`、`analysis_presenter.py`、测试与文档。

## Business logic

业务分析人员可以直接问毛利率最高的商品品类。系统根据商品明细销售额和商品成本表计算品类毛利率，执行只读查询并返回排名结论。

## Data contract

- `SalesTrendParameters.metric` 扩展为 `category_gross_margin`。
- `AnalyzeResponse.rows[].date` 在本问题中表示商品品类。
- `AnalyzeResponse.rows[].refundRate` 在本问题中承载毛利率百分比，用于保持现有前端表格兼容。

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

- 当前成本口径使用 `product_costs.unit_cost`，由导入脚本基于商品重量合成生成，后续可替换为真实成本数据。
- V1 为兼容前端，将毛利率复用到 `refundRate` 展示字段，后续应支持动态列名。
