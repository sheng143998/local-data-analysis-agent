# 模块：一百条查询顺序验证报告

## 执行结果

- 模式：严格顺序执行。每条先完成 Inspector、Guard、EXPLAIN 和 PostgreSQL 只读执行，再原子写入 `eval/reports/sequential_hundred_query_validation.json` checkpoint 后进入下一条。
- 总计：`100/100` 完成，`100` 通过，`0` 失败。
- 性能：平均 `365.9ms`/条，最大 `712ms`/条。
- 本地 JSON 报告仅作运行工件，不提交。

| 多表模式 | 条数 | 通过 | 平均耗时 |
| --- | ---: | ---: | ---: |
| 订单-支付：已支付订单数 | 10 | 10 | 286.3ms |
| 订单-支付：已支付销售额 | 10 | 10 | 262.7ms |
| 订单商品-商品：品类销售额 | 10 | 10 | 317.2ms |
| 订单-支付-商品明细-商品：品类订单商品数与销售额 | 10 | 10 | 348.7ms |
| 订单商品-商品-成本：品类毛利率 | 10 | 10 | 335.5ms |
| 订单-退款：年度退款订单率 | 10 | 10 | 286.3ms |
| 用户-订单：城市订单数排行 | 10 | 10 | 491.3ms |
| 用户-订单：有最小订单数门槛的城市客单价 | 10 | 10 | 469.5ms |
| 用户-订单：复购用户阈值统计 | 10 | 10 | 621.5ms |
| 流量-订单：年度访问到下单转化率 | 10 | 10 | 239.6ms |

## 实现与决策

- 新增 `eval/scripts/run_sequential_hundred_query_validation.py`。它固定顺序执行、每 case checkpoint、支持 `--resume`，并且没有并发或集合式 SQL 执行。
- 100 条由十个业务模式各十个独立参数变体组成。空时间范围和空流量表产生的 `NULL` 或空聚合属于有效业务结果，不算失败。
- 本轮未出现新的确定性错误。此前修复的“已支付”过滤标准化和 Guard 对 `COUNT(*)` 的处理在本轮持续通过。

## 验证

- `python -m pytest backend/tests/test_sequential_hundred_query_validation.py backend/tests/test_sql_validation_tools.py backend/tests/test_sql_inspector.py -q`：`21 passed`。
- 真实顺序运行：`python eval/scripts/run_sequential_hundred_query_validation.py --report eval/reports/sequential_hundred_query_validation.json`：`100/100 passed`。
- 最终回归、前端构建和差异检查结果见本模块提交前验证记录。

## 风险

- 本报告覆盖确定性 SQL 安全与执行链路，不等同于云端模型 100 次生成质量。模型超时、空 SQL 或非 JSON 仍须由独立模型可用性评估跟踪。
- 测试 SQL 仅用于评估脚本，不进入应用主链路，不构成固定 SQL 兜底。

## 交付

- 实现提交：`a61010a`（`新增百条顺序查询验证`）。
- 推送：已推送至 `origin/main`。
