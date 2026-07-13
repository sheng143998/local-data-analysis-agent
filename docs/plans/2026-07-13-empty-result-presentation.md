# 空结果语义展示计划

## Goal

将成功执行但返回空结果集与模型、Guard、Executor 失败明确区分，使 Presenter 基于已解析的度量和时间筛选生成准确空数据说明，而不将 `0` 数值误判为空数据。

## Scope

- 依据 `SqlExecutionResult.status` 与 `row_count` 确定展示结果状态。
- 对成功空结果生成包含查询度量和 Query Plan 时间范围的说明，并在响应来源中提供机器可读状态。
- 保留已有失败摘要路径；0 值的聚合行仍作为正常数据结果展示。
- 补充 Presenter/Result Contract 聚焦测试。

## Out of scope

- 不修改 Executor、SQL Memory、SQL Guard、模型 Prompt 或 SQL 生成。
- 不将空结果改写为业务原因推断，也不增加固定 SQL。
- 不改前端页面或公开 API 的必填字段。

## Implementation steps

- [x] 提炼 Presenter 的结果状态与空结果摘要。
- [x] 将内部 Contract 时间范围用于空结果说明。
- [x] 增加空结果、零值和执行失败的回归测试。
- [x] 运行聚焦测试；包含 API 测试的组合命令在 120 秒上限未完成，未计为通过。
- [x] 完成模块记录、handoff、提交和推送。

## Validation plan

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_analysis_presenter.py backend/tests/test_result_contract_builder.py -q`
- `npm.cmd run eval:standard`（若模型运行时间超过可用窗口，保留已有 authenticated full report 并明确记录）。

## Risks

- 空结果只说明没有符合已执行筛选的记录，不能断言上游数据不存在或业务为零。
- 响应来源字段新增状态值必须保持向后兼容，前端未消费时不能影响既有展示。
