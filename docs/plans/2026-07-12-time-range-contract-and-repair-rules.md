# Time Range Contract And Repair Rules

## Goal

将明确时间表达转换为可执行、可验证的半开区间，并把 SQL Guard 错误转换为模型可直接执行的修复规则，降低模型遗漏时间过滤或引用不存在字段的概率。

## Scope

- 为 `QuerySpec` 增加结构化时间边界和 SQL 过滤约束。
- 解析当天、指定日期、本月、指定月份和指定年份；区间统一为 `[start, end)`。
- 将时间约束传入 SQL Generator Prompt，并在 SQL 意图校验中检查时间范围是否被满足。
- 为 Guard 字段错误、未定义输出别名和时间范围错误生成明确 Repair 规则。
- 补充单元测试和模块完成记录。

## Out Of Scope

- 不修改数据库表结构或历史 SQL Memory。
- 不改变 Guard 的只读、表白名单和字段元数据安全边界。
- 本次不实现任意自然语言日期、时区配置或数据库方言扩展。

## Implementation Steps

- [x] 定义结构化时间约束和解析器。
- [x] 将约束接入 QuerySpec、模型 Prompt 和意图校验。
- [x] 将 Guard 错误归一为可复制 Repair 规则。
- [x] 增加 QuerySpec、Prompt 和分析图修复测试。
- [x] 运行 focused pytest 与全量后端测试；标准评测已尝试但超时。
- [x] 记录完成模块并更新 handoff。

## Validation Plan

- 运行 `npm.cmd run backend:test`。
- 运行 `npm.cmd run eval:standard`，记录结果和不可避免的模型波动。
- 检查 Prompt payload 中的时间边界与 Repair 规则。

## Risks

- 相对时间依赖运行日期；测试必须注入确定的 `today`，避免跨日不稳定。
- SQL 文本时间验证应保持保守：无法证明满足约束时应触发修复，而不是错误放行。
- 模型修复仍可能失败，Guard 必须继续作为最终安全边界。
