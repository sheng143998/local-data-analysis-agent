# SQL Runtime Safety And Model Baseline

## Completed

- SQL Guard now clamps any missing, non-literal, or oversized `LIMIT` to the configured `SQL_MAX_ROWS` value and blocks a focused denylist of PostgreSQL functions including `pg_sleep` and file-access helpers.
- SQL execution now starts an explicit `BEGIN TRANSACTION READ ONLY` transaction, applies `SQL_STATEMENT_TIMEOUT_MS` and `SQL_LOCK_TIMEOUT_MS`, then rolls back after reading results.
- User-facing execution errors now contain only the classified business summary; raw database errors remain in run diagnostics.
- `POST /api/analyze` returns `503` when the graph cannot produce executable SQL, rather than responding with `200` and an empty SQL string. Clarification responses remain normal `200` responses.
- Local/Ollama model calls now disable inherited environment proxies. This avoids a local request failing because a system SOCKS proxy is configured without `socksio`.
- API test SQL uses `EXISTS` for paid-order filtering where appropriate. The semantic validator now distinguishes a direct `JOIN payments` aggregation risk from a safe `EXISTS` filter.

## Configuration And Contract Impact

- Added `SQL_MAX_ROWS=30`, `SQL_STATEMENT_TIMEOUT_MS=15000`, and `SQL_LOCK_TIMEOUT_MS=3000` to `backend/.env.example`.
- Added `503` as the documented `/api/analyze` response when executable SQL cannot be generated.
- Runtime safety is application-level protection only. The current local connection account must still be replaced with a dedicated least-privilege read-only runtime role in a later database-governance module.

## Validation

- Focused Guard, Executor, API, graph, and model-adapter tests: `64 passed`.
- Full backend suite: `180 passed, 1 warning`.
- `npm.cmd run frontend:build`: passed.
- Standard evaluation rerun after disabling local proxy inheritance:
  - `9/20` execution success (`45%`).
  - `8/20` strict success (`40%`).
  - Average latency: `11329ms`.
  - The earlier transport failure caused by a missing SOCKS dependency is resolved.

## Remaining Risks And Next Step

- Eleven standard cases still fail: some produce `503` because the local model cannot generate valid SQL, while user, funnel, and coupon questions are currently classified as clarification requests. The next module should introduce a structured QuerySpec across intent parsing, prompt generation, validation, repair, SQL Memory, and AST-based evaluation.
- The standard evaluator still uses string matching for tables and keywords and needs AST/semantic assertions before becoming a quality gate.
- The runtime PostgreSQL role and test database remain shared local resources.
