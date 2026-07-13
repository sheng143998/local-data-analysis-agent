# Result Contract 可视化规格与真实图表

## Completed behavior

- `AnalyzeResponse` 新增兼容字段 `visualization`，包含 `kind`、标题、真实字段名、数值单位和选择原因。
- `build_visualization_spec()` 只检查已确认的 Result Contract：日期/月维度使用折线图；有限的状态、方式、来源或类型构成使用环形图；最多 30 个类别使用柱状图；单值、空结果和高基数结果返回 `none`。
- `ResultChart` 不再读取 `frontend/src/data/mock.ts`。它使用响应中的真实 rows 和展示规格构造 ECharts option，并在 ChatPage 的当前助手分析结果中与真实结果表并列展示。
- 结果表保持为事实来源。图表不会改变 SQL、结果值、指标口径或自然语言摘要；重新打开当前历史会话只恢复已持久化的摘要，不伪造图表。

## Key decisions

- 不允许模型生成 ECharts option、字段名、颜色或图表类型，避免展示层成为模型不可信输出的入口。
- 数值、时间和类别识别均保守处理。结果存在空值、混合单位或无法确认的列角色时，选择 `none` 而不是猜测图表。
- `pie` 只用于有限类别的非百分比构成，比例、日期序列和高基数排行仍使用表格或其他确定性图形。

## API/data-contract impact

- `POST /api/analyze` 响应新增兼容的 `visualization` 对象，前端 `AnalysisResponse` 已同步；现有调用方可忽略该字段。
- `docs/api.md` 与 `docs/api_frontend_mapping.md` 已增加字段定义、前端消费边界和示例。
- 未新增路由、数据库迁移、模型调用或 SQL 执行行为。

## Validation

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_result_contract_builder.py backend/tests/test_analysis_presenter.py -q`：`9 passed`。
- `npm.cmd run frontend:build`：通过；Vite 提示入口包约 1.57 MB，属于现有 ECharts 体积风险，未阻断构建。
- Mock 扫描：`ChatPage.tsx`、`ResultChart.tsx`、`SqlPanel.tsx` 无 `data/mock`、`salesTrend` 或 `finalSql` 引用。
- `git diff --check`：通过。
- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_api.py -q`：本机 124 秒窗口超时，未产生可用通过结果；未为旧整链路测试放宽 SQL Guard。

## Remaining risks and follow-up

- 目前只覆盖当前分析响应的实时结果。消息持久化尚未保存 rows/visualization，历史会话恢复仍只显示摘要。
- 后续 SSE 模块应只在最终 `result` 事件携带完整 visualization，不能用模拟数据预先绘图。
- 需要后续浏览器登录 smoke 覆盖不同图表种类与小屏布局。

## Delivery

- 待本轮提交并推送；不会包含本地评测工件。
