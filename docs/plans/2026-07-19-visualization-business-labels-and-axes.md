# 图表业务标签与量纲坐标轴修复计划

## Goal

让图表使用用户可理解的业务字段标签而非数据库别名，并为金额、数量、比例等不同量纲分配独立坐标轴，避免销售额趋势因与订单数共轴而失真。

## Scope

- 扩展 `VisualizationSpec`，传递维度和指标的展示标签及各指标单位。
- 后端 Result Contract 基于 Query Plan/已知业务字段生成中文展示标签，不改变内部取数字段。
- 前端图表用展示标签渲染标题、图例、坐标轴和提示框；时间标签使用简洁日期/月格式。
- 多指标趋势图按单位拆分 Y 轴，金额与订单数不共享数值尺度。

## Out of scope

- 不改变 SQL、Query Plan、图表数据行顺序或数据库指标口径。
- 不允许模型提供任意 ECharts 配置、HTML 或脚本。
- 不增加 Mock 数据或新的图表库。

## Implementation steps

- [x] 定义并同步后端/前端 `VisualizationSpec` 展示标签与单位字段。
- [x] 基于业务字段和 Query Plan 生成确定性标签与单位。
- [x] 改造 ResultChart 的图例、时间标签、提示框和多 Y 轴系列配置。
- [x] 补充 Result Contract focused 测试和前端构建验证。
- [x] 使用真实月度销售额/订单数结果验证标签和双轴配置。

## Validation plan

- Result Contract 单测断言 `month`、`sales_amount`、`order_count` 分别生成“月份”“销售额”“订单数”，并标记货币/数量单位。
- 前端生产构建通过，TypeScript 契约同步。
- 真实查询响应的 visualization 字段包含业务标签和单位，图表配置为金额与数量分轴。

## Risks

- 未知 SQL 别名需要保守回退为可读字段名，不能凭空解释业务含义。
- 同单位多系列应共享坐标轴，异单位多系列才拆分，避免无意义的多轴图。
