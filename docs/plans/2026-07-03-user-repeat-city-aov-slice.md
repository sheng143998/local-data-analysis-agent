# 复购率 / 城市客单价查询切片计划

## Goal

让 V1 标准问题“最近 90 天复购率是多少？”和“每个城市的客单价是多少？”进入真实 `analyze` 链路，补齐用户维度和地域维度经营分析能力。

## Current task

当前正在做：复购率 / 城市客单价查询切片已完成，等待提交推送。

## Scope

- 包含：识别复购率、城市客单价问题，生成只读聚合 SQL，复用 Guard / Executor / Presenter / Memory 链路。
- 包含：补充单元测试、API 测试、README、模块文档和 handoff。
- 不包含：严格自然日过滤、动态前端列配置、真实 LLM SQL Generator。

## Module boundary

- 上游输入：用户自然语言问题、SQL Memory reuse plan、schema/metric retrieval context。
- 下游输出：兼容现有 `AnalyzeResponse` 的中文结论、SQL、结果表、来源和可信说明。
- 主要文件：`sql_template_tools.py`、`schema_retriever.py`、`analysis_presenter.py`、测试与文档。

## Business logic

业务分析人员可以直接问复购率或城市客单价。系统会基于用户、订单和支付数据计算整体复购率，或按城市聚合销售额、订单数和客单价。

## Data contract

- `SalesTrendParameters.metric` 扩展为 `repeat_purchase_rate` / `city_avg_order_value`。
- `AnalyzeResponse.rows[].date` 在本切片中表示“整体复购率”或城市名称。
- `AnalyzeResponse.rows[].refundRate` 在复购率问题中承载复购率百分比，在城市客单价问题中继续承载退款率，保持前端兼容。

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

- 当前复购率暂按全量已支付用户订单计算，未严格套用“最近 90 天”自然日窗口。
- V1 为兼容前端，将不同百分比指标复用到 `refundRate` 展示字段，后续应支持动态列名。
