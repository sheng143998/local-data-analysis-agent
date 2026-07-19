# 一百条查询顺序验证

## Goal

顺序生成并验证一百条多表只读查询，每条独立通过 Inspector、SQL Guard、EXPLAIN 与 PostgreSQL 只读执行；发现确定性问题时自主修复，输出逐条可追溯报告。

## Scope

- 创建串行验证器：每个 case 完成后立即原子写入 checkpoint，禁止并发和集合式执行。
- 使用十个多表业务模式各十个参数变体，覆盖订单-支付、商品-成本、退款-订单、用户-订单、流量-订单等关系。
- 对失败区分 SQL 口径/安全/执行问题与外部模型问题；仅修复确定性系统缺陷。
- 生成本地 JSON 结果与模块报告；JSON 为本地工件，不提交。

## Out of scope

- 不将一百条测试改为云端模型的一百次调用，避免模型超时掩盖 SQL 安全和业务验证结果。
- 不向应用主链路添加固定 SQL，不放宽 Guard 或只读执行限制。

## Implementation steps

- [x] 定义 100 条多表 case、预期实体和结果形态。
- [x] 实现逐条 checkpoint 验证器及 focused tests。
- [x] 顺序运行 100 条测试，诊断并修复可复现的问题后重测当前条。
- [x] 生成逐条报告和最终统计。
- [x] 完成回归、前端构建、文档更新、提交与推送。

## Validation plan

- 验证器 unit tests：case 数量、唯一 ID、逐条 checkpoint 和结果摘要。
- 真实顺序运行 100 条 case；每条记录 Inspector、Guard、EXPLAIN、执行状态、行数和耗时。
- `npm.cmd run frontend:build`、focused pytest 和 `git diff --check`。

## Risks

- 数据为空或时间范围无数据是合法业务结果，不应误报为执行失败。
- 数据库环境不可用时 checkpoint 要保留已完成条目，不能将未执行条目标为通过。
