# Result Contract And Presenter

## Completed behavior

- Graph 在执行后构造内部 Result Contract，包含 Query Plan、列角色、真实行、范围和告警。
- Presenter 优先使用计划度量展示标签，单值/分组/排行不再仅依赖问题关键词落入默认销售趋势。
- 对外 AnalyzeResponse 字段保持兼容。

## Validation

- Result Contract/Presenter/Graph focused `36 passed`。
- API/Presenter 回归 `4 passed`。
- 后端全量 `241 passed, 1 warning`。

## Remaining risks

- 前端暂未消费内部列角色；图表和结构化来源展示由后续 UI 专项完成。
