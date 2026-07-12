# Time Range Contract And Repair Rules

## Completed Behavior

- `QuerySpec` 现在保存 `time_start`、`time_end` 和 `time_filter`。
- 明确日期、明确月份、明确年份、当天和本月会被转换为半开区间 `[start, end)`；例如 2017 年为 `>= DATE '2017-01-01' AND < DATE '2018-01-01'`。
- 原始问题中的明确时间表达优先于意图模型返回的空或不完整 `time_range`。
- SQL Generator Prompt 会收到必需的时间谓词；SQL 意图校验要求 SQL 同时含有 `>= start` 与 `< end`。
- Repair Prompt 新增 `repair_rules`：字段不存在时要求先声明输出别名或改用原表达式；时间范围缺失时提供可直接替换时间字段的完整谓词。

## Key Decisions

- 使用半开区间而不是月末 `23:59:59`，避免不同月份天数、毫秒精度与时区边界错误。
- 时间校验仅要求模型使用指定的比较符与两个边界；Guard 继续负责 SQL 安全和真实字段存在性，不把业务语义校验混入 Guard。
- `最近 N 天`、上月、今年等未在本次范围内的表达不伪造固定边界，保留给后续相对时间解析模块。

## API And Data Contract Impact

- 内部 `QuerySpec` 和模型生成 payload 新增时间边界字段；外部 `/api/analyze` 响应契约不变。

## Validation

- Focused：`51 passed`，覆盖 QuerySpec、意图解析、模型 Prompt、分析图、Guard 和 Executor。
- Full backend：`npm.cmd run backend:test`，`188 passed, 1 warning`。
- `npm.cmd run eval:standard` 已启动，但 244 秒后超时，未覆盖旧的 `eval/reports/latest_eval_report.json`；没有可报告的新评测基线。

## Remaining Risks

- 时间谓词验证目前基于 SQL 文本比较符，后续可升级为 AST 谓词与字段血缘验证。
- 相对时间表达仍需注入统一业务时区和可测试的时钟。
- 本机模型逐题评测耗时过长，需要增加评测超时、单例重试和进度输出。

## Follow-up Work

- 在真实 `/api/analyze` 运行记录中验证“2017年卖了多少钱”能在一次 Repair 后成功。
- 增加按自然周、上月、今年、最近 N 天的统一时间解析。
