# 模块：通用分析结果 Presenter

当前状态：本模块已完成代码、测试、死代码清理和文档更新，并通过全量验证，已提交并推送到 GitHub。它不新增固定 SQL 模板，不改变 API 字段，不展示模型、数据库、SQL Memory 或向量调试信息。

业务逻辑：后续模型 SQL 生成会返回更多类型的结果列，Presenter 不能继续假设每个查询都有 `daily_sales`、`order_count`、`refund_rate`。本模块让结果总结基于真实返回列动态生成：识别维度列、数值列、比例列，生成摘要、指标卡和来源范围。

关键代码：

- `backend/app/tools/analysis_presenter.py`：新增 `ResultProfile` 和通用 helper，自动生成 `summary`、`metrics` 和 `source.range`，并移除旧 `_summary_text()` / `_row_label()` 残留。
- `backend/tests/test_analysis_presenter.py`：覆盖任意列结果和既有城市客单价结果的摘要/指标卡。
- `backend/tests/test_api.py`：现有 API 测试继续验证销售、订单、商品、品类、退款率、支付成功率、毛利率、复购率和城市客单价关键词不回退。

数据契约：

- 不新增 API 字段。
- `AnalyzeResponse.summary`：由真实结果列生成。
- `AnalyzeResponse.metrics`：最多 4 个指标卡，包含返回行数和主要数值列合计/均值。
- `AnalyzeResponse.rows`：仍保持 SQL Executor 原始结果列。

验证：

- `py -3 -m pytest backend/tests/test_analysis_presenter.py backend/tests/test_api.py`，12 passed，1 个 `StarletteDeprecationWarning`。
- `npm run backend:test`，111 passed，1 个 `StarletteDeprecationWarning`。
- `npm run frontend:build`，通过。
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。

风险/后续：

- 当前仍是确定性总结，不调用模型；复杂业务洞察后续可在 ModelAdapter 后面增加可控总结，但必须保留本模块的结构化 fallback。
- 对完全陌生列名会使用英文列名去下划线展示，后续可增加字段中文词典。
