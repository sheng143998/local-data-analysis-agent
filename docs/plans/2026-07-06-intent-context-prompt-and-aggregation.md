# 意图上下文 Prompt 与聚合口径修正计划

## Goal

修复“2017年卖了多少钱，平均卖了多少钱”这类问题中，总销售额和平均销售额没有被清晰区分、以及跨 `payments` join 后重复累计 `orders.total_amount` 的风险。继续保持方向为增强意图理解和通用 SQL 生成约束，不新增针对单个问题的固定 SQL 模板。

## Scope

包含：
- 将意图解析结果作为结构化上下文传入 SQL Generator prompt，而不是只拼接在自然语言问题里。
- 在 prompt 中明确常见指标语义：总销售额、订单数、客单价需要区分，客单价按订单去重计算。
- 增加订单金额与支付表 join 的聚合约束：如果使用 `payments` 过滤支付状态，必须先按订单去重或先聚合支付表，避免一单多支付导致 `orders.total_amount` 被重复求和。
- 优化意图模型失败后的降级策略：复杂多指标问题在启发式兜底置信度不足时反问确认，而不是直接进入 SQL。
- 增加 focused tests 覆盖 prompt payload、意图降级和重复聚合风险识别。
- 更新模块文档和 handoff。

不包含：
- 不写真实 `INTENT_MODEL_API_KEY`。
- 不把专用意图模型直接作为 SQL 放行依据。
- 不新增固定 SQL 模板或单 case 强制 SQL 覆盖。
- 不修改前端 UI。

## Implementation steps

- [x] 创建本计划文档。
- [x] 扩展 SQL Generator payload，加入 `question_intent` 和 `metric_semantics`。
- [x] 在 analysis graph 中把意图上下文传给模型 SQL Generator 和修复请求。
- [x] 增加 SQL 意图校验，识别 `orders.total_amount` 与多行 `payments` join 的重复聚合风险。
- [x] 优化 heuristic fallback 的复杂问题置信度与澄清策略。
- [x] 更新 focused tests。
- [x] 运行 focused tests。
- [x] 补模块完成文档并更新 handoff。

## Validation plan

- `.venv\Scripts\python -m pytest backend\tests\test_question_intent_parser.py backend\tests\test_model_sql_generator.py backend\tests\test_analysis_graph_sql_selection.py`

## Risks

- Prompt 约束可以显著降低模型犯错概率，但不能替代 SQL Guard；重复聚合类问题需要在意图校验阶段继续拦截。
- 如果用户未配置真实专用意图模型，系统仍会回到启发式解析，复杂口语问题会更倾向于反问确认。
