# QuerySpec Semantic Contract

## Completed

- Added typed `QuerySpec` with metrics, dimensions, time range, granularity, ranking requirement, explicit Top N, required table groups, output tokens, and forbidden SQL patterns.
- Added deterministic semantic mappings for new users, ordering users, user purchase ranking, visit-to-order conversion, cart-to-payment conversion, coupon redemption, coupon AOV comparison, and traffic-source order conversion.
- Intent parsing now attaches QuerySpec and recognized user, funnel, coupon, and source questions no longer fall into the generic clarification path solely because the previous metric list was incomplete.
- SQL generator prompts now receive the compact QuerySpec alongside intent, retrieved schema, metrics, relationships, and reuse plan.
- SQL validation and SQL Memory verification use QuerySpec requirements when available.
- Successful SQL Memory writes now save actual SQL-referenced tables and QuerySpec metrics/dimensions instead of all retrieved tables and a fixed `order_date` dimension.
- Ranking semantics now distinguish a required `ORDER BY` from an explicit `LIMIT`; questions such as “最高” no longer incorrectly reject a valid top-10 result as exceeding `LIMIT 1`.

## Validation

- QuerySpec, parser, generator payload, Memory, and graph-focused tests passed.
- Full backend suite: `184 passed, 1 warning`.
- `npm.cmd run frontend:build`: passed.
- Standard evaluation baseline:
  - Execution success: `11/20` (`55%`), up from `9/20` (`45%`).
  - Strict success: `10/20` (`50%`), up from `8/20` (`40%`).
  - Average latency: `13056ms`.

## Remaining Risks And Next Step

- Nine cases now reach the model path but still return `503`: payment failure, monthly refund rate, gross margin, ordering users, user purchase ranking, two funnel conversions, coupon redemption, and coupon AOV comparison.
- The remaining strict failure is repeat rate; the evaluator expects `users` and `repeat_rate`, while a valid implementation can derive repeat behavior from `orders.user_id`. The evaluator needs AST-aware alternative semantics before it can be a strict quality gate.
- Next module should enrich complex-metric formula guidance and repair prompts from QuerySpec, then replace string-only evaluation assertions with AST/semantic checks.
