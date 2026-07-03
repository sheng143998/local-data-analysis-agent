# SQL Memory 复用表/意图约束计划

当前正在做：SQL Memory fast_path 表/意图约束已完成实现、测试、评估和文档更新，等待提交并推送。

## Goal

标准问题评估断言显示 20/20 链路成功，但严格成功率只有 55%。主要问题是 SQL Memory `fast_path` 对相似问题复用了缺少关键业务表的 SQL。本模块先增加确定性表/意图约束：问题明显要求某些业务表时，候选 SQL 必须包含这些表才能进入 `fast_path`。

## Scope

- 包含：
  - 根据中文问题推断 fast_path 必须命中的关键表。
  - SQL Memory 候选增加 `required_table_match`。
  - `plan_sql_reuse()` 只有在高分且关键表匹配时才走 `fast_path`。
  - 增加单元测试和评估回归。
  - 更新 README、模块说明和 handoff。
- 不包含：
  - 完整 embedding / pgvector 召回。
  - 通用意图分类模型。
  - 修复所有语义断言失败。

## Module Boundary

- 上游输入：用户问题、SQL Memory 候选。
- 核心处理：用问题关键词推断关键表，并检查候选 `final_sql` 是否包含这些表。
- 下游输出：更保守的 `SqlReusePlan`。

## Business Logic

- 对“新增用户/下单用户/购买次数”这类问题，fast_path SQL 应包含 `users`。
- 对“访问/加购/流量来源/转化率”这类问题，fast_path SQL 应包含 `traffic_events`。
- 对“优惠券/核销”这类问题，fast_path SQL 应包含 `coupons` 或 `coupon_usages`。
- 如果候选 SQL 不满足关键表要求，即使文本相似度高，也不能直接复用为 fast_path。

## Data Contract

- `SqlMemoryCandidate.required_table_match: bool`
- `SqlMemoryCandidate.required_tables: list[str]`
- `SqlReusePlan` 保持不变。

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 实现 required table 推断和 fast_path gating。
- [x] 添加单元测试。
- [x] 运行标准问题评估并更新文档。
- [~] 提交并推送。

## Validation Plan

- `npm run backend:test`
- `npm run eval:standard`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and Open Questions

- 关键词规则仍是启发式，后续应升级为 intent/schema 混合判断。
- 部分指标可以不显式 join 维表也能计算，过严规则可能降低 fast_path 命中率，但优先保证不错误复用。
