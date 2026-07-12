# 模型语义候选优先计划

## Goal

修正意图解析中“未知指标候选立即澄清”的硬限制。语义模型可用且高置信时，应保留模型提取的业务候选并交给检索与 SQL 生成；受控 `metrics` 只用于已定义口径、校验和降级策略。

## Scope

- 在 `ParsedQuestionIntent` 中保存模型自然语言指标和维度候选。
- 高置信未知候选不再单独触发澄清，除非模型明确要求澄清或置信度不足。
- 将候选透传到 SQL Generator Prompt，供 schema 召回与 SQL 模型理解用户语义。
- 保持模型故障时的启发式/词表降级、QuerySpec、SQL Guard 和只读 Executor。
- 更新测试、文档、handoff 并提交推送。

## Out of scope

- 不允许模型候选绕过 SQL Guard 或执行任意 SQL。
- 不把未知候选自动写入指标定义或长期口径库。
- 不新增 `total_user_count` 固定指标定义；本模块验证通用语义通路。

## Implementation steps

- [x] 扩展意图契约并保留模型自然语言候选。
- [x] 调整高置信未知候选的澄清条件。
- [x] 将语义候选传入 SQL Generator Prompt。
- [x] 补充模型优先、模型故障降级和 Prompt 透传测试。
- [x] 执行 focused pytest、后端全量和标准评测。
- [x] 记录完成状态并提交推送。

## Validation plan

- `py -3 -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_model_sql_generator.py`
- `npm.cmd run backend:test`
- `npm.cmd run eval:standard`

## Risks

- 未定义语义缺少 QuerySpec 的强业务口径，SQL 质量更依赖模型、schema 召回和 Guard。
- 高置信错误理解可能进入 SQL 生成，但仍会受白名单表字段、只读和 Guard 限制。
