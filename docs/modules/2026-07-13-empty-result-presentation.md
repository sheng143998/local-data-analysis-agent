# 空结果语义展示

## Completed behavior

- Result Contract 将成功零行标记为 `empty`，成功但返回聚合 0 值的一行仍标记为 `success`。
- 分析响应 source 新增向后兼容的 `resultState`，可取 `success`、`empty`、`error` 或 `blocked`。
- Presenter 对空结果说明为“当前筛选条件下没有匹配记录”，不推断数据源不存在或业务值为零。

## API and data-contract impact

- `AnalysisSource.resultState` 是带默认值的新增字段，既有客户端可忽略。
- 无数据库、SQL、模型或安全边界变更。

## Validation

- `.venv\\Scripts\\python -m pytest backend/tests/test_analysis_presenter.py backend/tests/test_result_contract_builder.py`：`5 passed`。
- 加入 `backend/tests/test_api.py` 的组合命令在 120 秒上限未完成，未计为通过。

## Remaining risks

- 前端暂未专门渲染 `resultState`，但既有文本摘要已能表达空结果。
- 澄清响应当前使用 `blocked` 表示未执行查询；未来若前端需要，可增加独立等待确认状态。
