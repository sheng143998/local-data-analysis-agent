# 模块：Schema 主题表召回增强

当前状态：本模块已完成代码开发、文档更新、完整验证、commit 和 push。提交信息为 `增强Schema主题表召回并通过验证`，已推送到 GitHub。该模块不新增固定 SQL 模板，不改变普通用户前端，不改变 `/api/analyze` 响应契约。

业务逻辑：当用户提出用户、流量、优惠券、退款、毛利、商品等主题问题时，Schema Retriever 会把相关业务表字段纳入上下文。例如“访问转化率”召回 `traffic_events`，“优惠券核销率”召回 `coupons` / `coupon_usages`，“购买次数最多的用户”召回 `users` / `orders`。这让后续 SQL 生成能基于真实表字段工作，而不是因为上下文缺表只能围绕订单表生成。

关键代码：

- `backend/app/tools/schema_retriever.py`
  - 新增 `SCHEMA_TOPIC_TABLES`，把业务主题词映射到相关表列表。
  - `_related_tables()` 改为遍历主题表规则，保留指标依赖表优先和 `orders` 默认兜底。
  - 新增用户、流量、优惠券主题表召回，覆盖 `users`、`traffic_events`、`coupons`、`coupon_usages`。
- `backend/tests/test_retrieval_tools.py`
  - 新增流量、优惠券、新增用户和 Top 用户召回测试，验证真实 `retrieve_schema()` 能返回相关字段。

数据契约：

- API 响应不变。
- 数据库结构不变。
- 后端内部 `RetrievalContext.tables` / `fields` 在相关问题下会包含更多真实业务表字段。

验证：

- `py -3 -m pytest backend/tests/test_retrieval_tools.py`，12 passed。
- `npm run backend:test`，155 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- 抽查 `eval/reports/latest_eval_report.json`：当前断言失败中的 `users`、`traffic_events`、`coupons`、`coupon_usages` 均为 `present_in_context`，说明缺失表已进入上下文；严格率未提升，下一步应修 SQL 生成/复用策略。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 本模块只解决 schema 上下文召回，不保证当前确定性 SQL 生成会使用这些表。
- 下一步应优先处理 SQL Memory 复用或确定性 rewrite 没有利用已召回 `users`、`traffic_events`、`coupons`、`coupon_usages` 的问题。
