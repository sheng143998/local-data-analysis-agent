# 通用分析结果 Presenter 计划

## Goal

把当前偏销售模板的自然语言总结和指标卡，升级为能根据 SQL Executor 返回的真实列动态生成。这样后续模型 SQL 生成更多类型查询时，不需要继续为每个业务模板手写总结逻辑。

## Current task

当前正在做：通用 Presenter 已完成实现、清理旧总结函数、通过验证并已提交推送。

## Scope

包含：

- 根据 `execution.rows` 和 `execution.columns` 自动识别维度列、数值列、百分比列。
- 生成通用中文总结，包含返回行数、主要维度、首行结果、核心数值合计/均值。
- 生成最多 4 个指标卡，来自真实结果列。
- 保留现有 `AnalyzeResponse` 字段，不改前端类型和 API 路径。
- 增加 focused tests。
- 更新 README、Agent 工作流、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不接入模型生成自然语言。
- 不改变普通用户前端布局。
- 不展示模型、数据库、SQL Memory 或向量调试信息。

## Module boundary

上游输入：

- `SqlExecutionResult.columns`
- `SqlExecutionResult.rows`
- 用户问题
- `RetrievalContext`
- `SqlReusePlan`

下游输出：

- `AnalyzeResponse.summary`
- `AnalyzeResponse.metrics`
- `AnalyzeResponse.source.range`

预计触达文件：

- `backend/app/tools/analysis_presenter.py`
- `backend/tests/test_analysis_presenter.py`
- `README.md`
- `docs/agent_workflow.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-generic-analysis-presenter.md`

## Business logic

业务用户不应该因为系统内部 SQL 模板不同而看到不匹配的总结。只要查询返回了表格，系统就应该能基于真实列说明“查到了什么、第一行/最高项是什么、核心数值是多少”，并继续展示 SQL 和来源。

## Data contract

不新增 API 字段。仍使用：

- `AnalyzeResponse.summary`
- `AnalyzeResponse.metrics`
- `AnalyzeResponse.rows`
- `AnalyzeResponse.source`

内部 helper 输出：

- `ResultProfile.dimension_column`
- `ResultProfile.metrics`
- `ResultProfile.range_label`

## Implementation steps

- [x] 读取 handoff、Presenter、analysis schema 和 API 测试。
- [x] 实现通用结果画像和总结 helper。
- [x] 接入 `present_sales_trend_result()`。
- [x] 增加 focused tests。
- [x] 更新文档和模块完成说明。
- [x] 运行验证。
- [x] 清理旧 `_summary_text()` / `_row_label()` 死代码。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_analysis_presenter.py backend/tests/test_api.py`，12 passed，1 个 `StarletteDeprecationWarning`
- `npm run backend:test`，111 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- 当前仍是确定性总结，不调用模型；复杂洞察后续可接 ModelAdapter，但必须保留结构化 fallback。
- 指标卡来自结果列，可能不如人工模板精细，但能覆盖更广 SQL 返回形态。
- 现有销售类总结关键词需要保持，避免前端和测试基线倒退。
