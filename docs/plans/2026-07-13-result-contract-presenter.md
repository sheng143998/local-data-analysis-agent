# Result Contract And Presenter

## Goal

使用 Result Contract 将已解析语义、Query Plan、执行列/行、范围和告警传递给 Presenter，按结果形态而非固定销售模板生成用户结论。

## Scope

- 定义内部 Result Contract 与构建工具。
- Graph 在执行成功后构造 Contract，Presenter 优先使用 Contract 的 plan/columns。
- 覆盖单值、分组、排行和空结果摘要。

## Out of scope

- 不改变公开 API schema、不增加图表或前端页面。

## Implementation steps

- [x] 定义 Contract/Builder。
- [x] 接入 Presenter 与 Graph。
- [x] 测试、全量验证、文档、commit、push。

## Validation plan

- Presenter/Result Contract/Graph focused tests，后端全量。

## Risks

- 列别名不可控时必须使用安全通用标签，不能猜业务指标。
