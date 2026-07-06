# 意图上下文 Prompt 与聚合口径修正

## 背景

用户问题“2017年卖了多少钱，平均卖了多少钱”暴露出两类风险：

- 意图理解虽然能归一化问题，但 SQL Generator prompt 里没有拿到结构化意图，只能从自然语言里自行猜“总额”和“平均值”。
- 当模型为了判断已支付订单而 JOIN `payments` 时，如果直接 `SUM(orders.total_amount)`，一单多支付会把订单金额重复累计。

本模块继续沿用“更强意图模型 + 通用约束 + SQL Guard/Validator”的方向，不新增固定 SQL 模板。

## 改动内容

- `model_sql_generator`：
  - `build_sql_generation_payload()` 新增 `question_intent`，只传递 normalized question、metrics、dimensions、filters、time_range、confidence、source 等安全结构化字段。
  - 新增 `metric_semantics`，明确：
    - `sales_amount` = 总销售额 / 一共卖了多少钱，订单粒度。
    - `order_count` = `COUNT(DISTINCT orders.id)`。
    - `avg_order_value` = `SUM(orders.total_amount) / COUNT(DISTINCT orders.id)`。
  - prompt requirements 新增约束：总销售额和平均销售额必须分别输出；JOIN `payments` 后汇总订单金额必须先按订单去重或先聚合支付表。
- `analysis_graph`：
  - 将 `question_intent` 透传给模型 SQL 生成和 repair prompt。
  - `_sql_intent_warnings()` 新增重复聚合风险检查：识别 `JOIN payments` 后直接 `SUM(o.total_amount)` 的 SQL，并要求改为订单去重或支付表预聚合。
- `question_intent_parser`：
  - 启发式兜底新增“平均卖了多少钱 / 平均卖了多少”到 `avg_order_value` 的映射。
  - 模型失败且问题呈现复杂多指标但启发式未解析完整时，降低置信度并触发澄清。

## 验证

已运行：

```powershell
.venv\Scripts\python -m pytest backend\tests\test_question_intent_parser.py backend\tests\test_model_sql_generator.py backend\tests\test_analysis_graph_sql_selection.py
```

结果：`42 passed`。

## 说明

这次没有写入真实 `.env` 密钥，也没有新增单问题固定 SQL。真实效果仍依赖用户配置更强的 `INTENT_MODEL_*` 和 SQL 生成模型；即便模型输出错误 SQL，重复聚合风险也会在意图校验阶段被拦截并触发 repair。
