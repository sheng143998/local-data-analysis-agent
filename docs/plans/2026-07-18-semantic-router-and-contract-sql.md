# 语义 Router 与合同 SQL 强制改造

## Goal

将对话分流升级为安全规则优先、受限语义分类、确定性复核和保守降级，使普通聊天不因单个业务词误入 SQL Agent；将 SQL 生成升级为在已确认 Semantic Contract 与 Query Plan 下生成并验证合法业务口径的 SQL。

## Scope

- 新增不含 schema、SQL 或结果行的 Router 语义分类器，要求结构化输出角色、置信度和依据。
- 保留危险请求和待澄清会话的确定性优先级；模型失败或低置信度时仅明确数据查询可进入 Graph，其他默认普通聊天。
- 增加 Router 的确定性数据证据复核和结果解释复核，避免单词命中造成误路由。
- 扩展 Query Plan/Inspector，使已解析的实体、指标、维度、筛选、排序、Top N、输出形态和指标公式成为 SQL 生成后的阻断条件。
- 删除主链路中的固定订单数 SQL fallback；不满足合同的 SQL 只能受控 Repair 或失败，不能改写成固定业务回答。
- 新增 focused 单元测试、10 条意图分类测试；重测上次 50 case 的答案/严格失败集和稳定随机 5 条。

## Out of scope

- 不修改数据库 schema、鉴权协议或前端 API。
- 不允许 Router、通用对话模型或 SQL 模型直接访问数据库。
- 不把未经审核的历史 SQL 直接执行，也不绕过 Inspector、Guard、EXPLAIN 或只读 Executor。
- 不声称或复刻未公开的 ChatGPT 内部实现；仅采用公开的结构化分类、保守回退和语义层模式。

## Implementation steps

- [x] 调研并记录公开结构化分类与语义层实践，确认安全边界。
- [x] 实现 Router 语义分类、确定性复核与模型不可用回退，补 focused 测试和 10 条分类测试。
- [x] 记录 Router 模块、更新 handoff，提交并推送。
- [ ] 强化 Query Plan/Inspector 的合同覆盖校验，移除固定 SQL fallback，补 focused 测试。
- [ ] 运行历史失败 case 与稳定随机 5 条真实评测，记录结果和环境限制。
- [ ] 记录合同 SQL 模块、更新 handoff、提交并推送。

## Validation plan

- `pytest backend/tests/test_dialogue_router.py backend/tests/test_question_intent_parser.py -q`。
- 10 条固定意图样本，覆盖普通聊天、数据查询、结果解释、概览澄清和越权请求；模型可用时记录模型判定，模型不可用时验证保守回退。
- `pytest backend/tests/test_sql_inspector.py backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_query_planner.py -q`。
- 对 `sql_model_replacement_full_eval_20260714.json` 中答案不匹配或严格失败的 case 建立临时 UTF-8 数据集，并从 50 case 稳定选择 5 条额外样本运行真实评测。
- `git diff --check`；评测报告属于本地工件，不提交。

## Risks

- 语义 Router 的模型输出仅是路由建议，绝不能成为数据库访问授权；数据访问仍需要确定性证据和后续 SQL 安全链路。
- 模型服务超时、账号或网络问题会影响真实评测，必须与功能错误分开记录。
- 现有 Semantic Contract 覆盖未完整，未知口径应拒绝或澄清，不能伪造公式。

## Research references

- OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs
- Snowflake Semantic Views: https://docs.snowflake.com/en/user-guide/views-semantic/overview
- dbt Semantic Layer: https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-sl
