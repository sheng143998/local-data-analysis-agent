# SQL 准确率与路由延迟优化

## Goal

为 SQL 评测增加结构化结果行断言，并让明确的数据请求绕过无增益的 Router 模型调用，以提升准确率可测性和端到端响应速度。

## Scope

- `EvalCase` 支持 `expected_rows` 与严格行结果比较，不再只依赖文本 token。
- 新增结构化 SQL 准确率 smoke 数据集和 row comparator tests。
- 明确数据查询在安全证据充分时由 Dialogue Router 确定性进入 `data_analysis`，不调用 Router 模型；普通聊天、结果解释和模糊请求仍保留原有边界。
- 运行 focused tests、真实 API 性能抽样、前端构建。

## Out of scope

- 不降低 SQL 模型超时、不增加固定 SQL、不跳过意图、合同、Inspector、Guard 或 Executor。
- 不将一次模型调用的偶然成功表述为整体准确率。

## Implementation steps

- [x] 增加结构化行断言与 SQL 准确率 smoke 数据集。
- [x] 为明确数据请求增加 Router 快速路径与回归测试。
- [x] 运行结构化评测/真实 API 性能抽样。
- [x] 更新报告、交接、提交与推送。

## Validation plan

- Eval runner/Router focused pytest。
- 对已知多表问题运行真实 API，验证 SQL、结果行和 Router 调用数。
- 前端构建与差异检查。

## Risks

- 结构化行比较需要明确数值、日期与空值规范化，不能使用字符串偶然匹配。
- 快速路径只能用于已有直接数据证据的请求，避免把产品讨论错误送入数据库。
