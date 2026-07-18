# 语义 Dialogue Router

## Completed behavior

- Router 现在先处理越权请求和待澄清会话，再通过独立的受限语义分类调用区分 `general_chat`、`data_analysis` 与 `explain_result`。
- Router 模型只接收当前问题和两个会话状态布尔值，不接收 schema、SQL、查询结果行、提示词或密钥。
- 模型的路由建议必须满足确定性复核：数据分析需要明确数据请求证据，结果解释必须引用当前会话已完成的分析；否则保守降级为普通聊天。
- 明确的数据对象加查询/统计/查看表达在模型不可用时仍可进入既有澄清和 SQL 安全链路；仅有“用户体验”等产品讨论不会因“用户”一词访问数据库。
- Router 使用 intent 模型路由配置，新增独立开关、20 秒超时和零重试，避免 Router 请求占用 SQL 模型调用预算。

## Key decisions

- 不宣称或复刻未公开的 ChatGPT 内部实现；设计采用公开可验证的结构化分类、置信度阈值、确定性策略和保守回退模式。
- 模型分类不构成数据库访问授权。任何 `data_analysis` 后续仍必须经过意图解析、Semantic Contract、Query Plan、Inspector、Guard、EXPLAIN 和只读 Executor。
- 结果解释优先使用会话 `CurrentAnalysis` 的完成状态，避免“解释”一词拦截新的明确数据查询。

## API and contract impact

- 不改变对外 API。`DialogueDecision` 内部新增 `confidence` 和 `source`，用于编排和测试诊断。
- 新增 `ROUTER_MODEL_ENABLED`、`ROUTER_MODEL_TIMEOUT_SECONDS`、`ROUTER_MODEL_MAX_RETRIES` 配置说明。

## Validation

- `python -m pytest backend/tests/test_dialogue_router.py backend/tests/test_question_intent_parser.py -q`：`23 passed`。
- `python eval/scripts/run_router_eval.py --report eval/reports/router_semantic_eval_20260718.json`：10 条中文样本 `10/10`；模型分类 9 条，确定性结果解释 1 条，无回退。
- 云端最小结构化请求：`qwen3.7-plus` 在 Router 原 8 秒超时下发生 read timeout；使用 45 秒诊断上限约 12.7 秒成功，故 Router 默认超时上调为 20 秒。此前出现的 `Arrearage` 400 属于外部账户状态，未记为路由质量错误。
- `git diff --check`：通过。

## Remaining risks

- 云端模型首请求延迟仍可能接近 Router 超时；超时会安全降级，但会降低模糊表达的分类精度。
- 当前 10 条样本是固定冒烟集，后续应从真实匿名路由日志中审核扩展，防止过拟合词汇表达。

## Delivery

- 本模块提交与推送将在 SQL 合同模块开始前完成；评测 JSON 仅作为本地工件，不提交。
