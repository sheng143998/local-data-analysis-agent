# 综合 Agent 两百条测试用例

## Goal

生成并验证 200 条覆盖数据分析与普通聊天完整边界的测试用例集，使 SQL 生成正确性不再是唯一质量信号。

## Scope

- 新增独立 JSONL schema，表达路由目标、是否访问数据库、是否需要 SQL、是否需要澄清、会话前置状态和安全断言。
- 覆盖数据分析、普通聊天、结果解释、澄清、受限操作拒绝、会话补充与 API/所有权边界七类场景。
- 生成确定性 200 条数据集，提供 schema/数量/八类分类分布验证器和 focused tests。

## Out of scope

- 不执行 200 次云端模型调用，也不将这套跨路由用例强行塞入仅支持 SQL 断言的现有 `run_eval.py`。
- 不改变对话路由、SQL Guard 或鉴权行为；本模块只建立可执行测试资产和质量契约。

## Implementation steps

- [x] 定义综合 case schema、类别配额和断言字段。
- [x] 实现生成器与验证器，生成 200 条 JSONL 用例。
- [x] 添加 focused tests，验证数量、ID、八类分布和安全/路由必填字段。
- [x] 生成覆盖报告，完成回归、文档、提交和推送。

## Validation plan

- 生成器验证 200 条唯一 case、七类场景配额、路由和安全断言完整性。
- `pytest` 运行用例集 focused tests；`npm.cmd run frontend:build` 和 `git diff --check`。

## Risks

- 用例集定义的是可测试契约，不应因模型非确定性而标记为已经通过运行时评测。
- 后续执行器必须按 `expected_route` 分流，绝不能让普通聊天和拒绝类 case 进入数据库。
