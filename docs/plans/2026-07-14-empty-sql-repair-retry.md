# 空 SQL 的受控修复重试

## Goal

当 SQL 模型返回成功响应但缺少可执行 SQL 时，复用已有 Repair Prompt 尝试一次受控重试，减少格式性空 SQL，而不增加固定 SQL 或绕过安全链路。

## Scope

- 第一次空 SQL 也进入一次 `repair_model_sql`，修复上下文显式包含空 SQL 错误和 Query Plan。
- 第二次空 SQL 仍按既有失败路径处理。
- 验证重试次数上限、Repair Prompt 传参、Guard 路由和模型成功路径。

## Out of scope

- 不写实体或指标专用 SQL 模板。
- 不执行模型未经 Inspector、Guard、EXPLAIN 和只读 Executor 验证的 SQL。
- 不改变普通聊天、澄清、模型路由配置或数据库结构。

## Implementation steps

- [x] 调整空 SQL 的图路由和失败判定。
- [x] 新增一次空 SQL 重试与第二次终止的 focused tests。
- [x] 运行 Graph/SQL generator 回归与认证评测抽样。
- [x] 记录、提交并推送。

## Validation plan

- `backend/tests/test_analysis_graph_sql_selection.py` 和 SQL generator focused pytest。
- 已认证真值集失败样本的独立抽样评测，不覆盖既有工件。
- `git diff --check`。

## Risks

- 空 SQL 会多一次模型调用；只在首次失败时触发，第二次严格终止，避免无界重试和延迟放大。
