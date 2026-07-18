# Top N、成本与比率合同修复

## Goal

修复结构性排序词误入业务过滤、成本总额缺少来源合同、退款率缺少展示格式以及复购用户数缺少严格计数约束的问题。

## Scope

- 从 Intent filters 中移除前 N、最高/最多、排序和时间粒度等非 WHERE 结构词。
- 新增成本、退款订单率和复购用户数的版本化合同，并将来源字段、聚合、输出形态和精度传入 Query Plan/Inspector/Presenter。
- 真实复测 `database_022/028/035/043` 及 `database_013` 对照。

## Out of scope

- 不写固定 SQL，不放宽 Guard，不修改数据库既有迁移。

## Implementation steps

- [x] 归一化结构性 filter，补 Planner 测试。
- [x] 添加新语义合同迁移与合同校验/展示测试。
- [x] 运行 focused tests 和真实 5 case。
- [x] 更新模块记录、handoff、提交并推送。

## Validation plan

- Planner、Inspector、Presenter、Graph focused pytest。
- 真实 5 case 报告，单独区分模型服务错误与语义错误。

## Risks

- 合同只约束已审核口径；缺少合同的问题不能通过 Prompt 猜测公式。
