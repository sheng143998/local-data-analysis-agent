# 模块：图表业务标签与量纲坐标轴修复

## 已完成行为

- `VisualizationSpec` 新增 `field_labels` 和 `field_units`。内部字段仍用于取数，但图表标题、图例和坐标轴使用确定性的业务展示标签。
- 结果合同可将 `month`、`sales_amount`、`order_count` 映射为“月份”“销售额”“订单数”，并识别销售额为货币、订单数为数量。
- 时间图表标题由通用“趋势”改为指标标题，例如“订单数、销售额趋势”；时间轴展示 `YYYY-MM` 或 `YYYY-MM-DD`，不展示 ISO 时区文本。
- `ResultChart` 为不同单位的系列分配独立 Y 轴，金额与数量不再共用数值尺度；同单位系列仍共享轴。

## 关键决策

- 标签和单位由后端已确认的 Result Contract 确定，模型不能注入图表配置或任意展示文字。
- 未知字段仅回退为下划线分词后的可读文本，不猜测业务含义。
- 图表仍只使用真实 `rows`、`x_field` 和 `y_fields`，标签改造不影响 SQL、指标计算或行顺序。

## API 与数据影响

- `AnalyzeResponse.visualization` 新增：
  - `field_labels: Record<string, string>`
  - `field_units: Record<string, 'number' | 'currency' | 'percent'>`
- 后端 Pydantic、前端 TypeScript、图表组件和 API 文档已同步。
- 不涉及数据库迁移、SQL 执行或模型配置。

## 验证

- `python -m pytest backend/tests/test_result_contract_builder.py backend/tests/test_analysis_presenter.py -q`：`11 passed`。
- `npm.cmd run frontend:build` 通过；仅有既有 bundle 大小提示。
- 真实 PostgreSQL 月度已支付订单数据的可视化契约：`kind=line`，标题“订单数、销售额趋势”，`field_labels` 为月份/订单数/销售额，`field_units` 为 `number`/`currency`，前端据此分为两个 Y 轴。

## 剩余风险与后续

- 图表单位目前根据审核字段名确定；复杂派生指标增加后应在语义合同中显式声明展示单位与标签。
- 自动化浏览器环境无法访问宿主机本地 Vite 服务，未生成图表截图；前端生产构建和真实可视化契约已验证。
