# Top N 商品/品类销售额查询切片计划

## Goal

让 V1 标准问题“销售额最高的前 10 个商品是什么？”和“哪个商品品类销售额最高？”进入真实 `analyze` 链路，继续扩大业务分析人员可直接提问的范围。

## Current task

当前正在做：Top N 商品/品类销售额查询切片已完成，等待提交推送。

## Scope

- 包含：识别 Top N、商品/品类维度、生成只读 SQL、接入现有 Guard/Executor/Presenter/Memory 链路。
- 包含：补充后端单元测试、API 测试、README、模块完成文档和 handoff。
- 不包含：真实 LLM SQL Generator、严格自然日窗口、前端复杂动态表格重构。

## Module boundary

- 上游输入：用户问题、SQL Memory reuse plan、schema/metric retrieval context。
- 下游输出：兼容现有 `AnalyzeResponse` 的自然语言结论、SQL、结果表、来源和可信说明。
- 主要文件：`sql_template_tools.py`、`sql_generation_tools.py`、`analysis_presenter.py`、`analysis_graph.py`、前端聊天页表头、测试与文档。

## Business logic

业务分析人员可以直接问商品或品类销售排行。系统会识别 Top N 和分析维度，生成商品/品类聚合 SQL，经过安全校验后执行，并返回排行结论和简洁结果表。

## Data contract

- `SalesTrendParameters.metric` 扩展为 `top_product_sales` / `top_category_sales`。
- 仍复用 `AnalyzeResponse.rows`，其中 `date` 字段在排行问题中承载商品或品类名称，保证前端兼容。
- `sql_memories.parameters` 写入 `days`、`granularity`、`metric`、`limit`。

## Implementation steps

任务清单：
- [x] 扩展参数解析和 SQL 渲染。
- [x] 接入生成工具和结果展示。
- [x] 补充测试。
- [x] 更新 README、模块文档、handoff。
- [x] 跑完整验证、提交并推送。

## Validation plan

- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and open questions

- V1 先使用 `order_items.price` 作为商品/品类销售额，避免订单总额在多商品订单中重复计算。
- 前端暂以兼容表格展示排行，后续可新增动态列配置提升体验。
