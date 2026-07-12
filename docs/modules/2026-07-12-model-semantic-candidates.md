# 模块：模型语义候选优先

## 完成行为

- `ParsedQuestionIntent` 新增 `semantic_metrics`、`semantic_dimensions`，保存语义模型输出的自然语言候选。
- 高置信模型返回“用户总数”“物流及时率”等未预定义候选时，不再因为无法映射 `metrics` 而固定澄清；候选进入后续检索和 SQL 模型。
- 已定义指标仍映射到 `metrics`，用于 QuerySpec、口径校验和确定性降级。
- SQL Generator Prompt 的 `question_intent` 已包含语义候选，模型可结合用户原问题、候选、召回 schema 和表关系生成 SQL。
- 语义模型故障或低置信时，仍按既有启发式/词表路径澄清；生成 SQL 仍必须通过 Validator、Guard 和只读 Executor。

## 关键决策

- `metrics` 不再承担“所有语义都必须预注册”的职责，它只表示项目已定义且可验证的标准口径。
- 未定义候选不自动变成数据库指标定义，也不自动放宽 QuerySpec；它只是让模型主路径继续理解并生成受安全边界约束的 SQL。

## 验证

- `backend/tests/test_question_intent_parser.py backend/tests/test_model_sql_generator.py`：`20 passed`。
- `npm.cmd run backend:test`：`211 passed, 1 warning`。
- 标准评测：280 秒完成，`13/20` 执行成功，`execution_success_rate=65.00%`，`strict_success_rate=60.00%`。

## 剩余风险

- 未定义指标没有显式 QuerySpec 业务口径，最终效果更依赖模型、schema 召回和 SQL Guard。
- “用户总数”的口径仍应在后续由业务确认，例如全部注册用户、活跃用户或已下单用户；本模块只解决模型被过早阻断的问题。
