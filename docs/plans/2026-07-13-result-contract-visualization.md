# Result Contract 可视化规格与真实图表

## Goal

基于已确认的 Result Contract、真实执行 rows 和列语义生成确定性图表规格，并在聊天结果中以 ECharts 呈现折线、柱状或环形图，替换数据问答路径的静态趋势 Mock。

## Scope

- 扩展 `AnalyzeResponse`，新增 `VisualizationSpec`，包含 kind、标题、字段、单位和选择原因。
- 后端根据 Result Contract/真实 rows 选择图表：日期或月份维度用 line；类别排行用 bar；不超过 8 类、非比例指标的组成用 pie；单值、空集、高基数或混合单位为 none。
- 重写 `ResultChart` 为真实 rows/spec 消费者，并在 ChatPage 的助手结果中显示。
- 保留结果表，图表不能替代真实数据表或改变 SQL/结果值。
- 为 builder/presenter 和前端构建补充验证。

## Out of scope

- 不让模型输出 ECharts option、字段名、颜色或图表类型。
- 不修改 SQL、Query Plan、Result Contract 原始结构、Guard 或 Executor。
- 不持久化完整图表 option 到会话消息；历史恢复仍以当前 response 摘要为界。

## Implementation steps

- [x] 定义公开 VisualizationSpec schema/type 与确定性 builder。
- [x] 在 Presenter 中写入响应并为无图表场景返回 `none`。
- [x] 重写 ResultChart，接入 ChatPage，删除静态趋势 Mock 依赖。
- [x] 增加单值、时间趋势、类别排行、组成和空结果的 focused tests。
- [x] 运行 pytest、frontend build、Vite smoke、文档/hand off/commit/push。

## Validation plan

- `pytest backend/tests/test_result_contract_builder.py backend/tests/test_analysis_presenter.py`。
- `npm.cmd run frontend:build`。
- 核对 ChatPage 和 ResultChart 无 `data/mock` 引用，`git diff --check` 通过。

## Risks

- SQL 行中的数值可能为字符串或 Decimal，builder 必须保守识别，不确定时返回 none。
- 饼图仅适合有限组成，不得用于比率、日期序列或高基数排行。
- 图表只是展示层，不得改变原始 rows、指标口径或 Answer Summary。
