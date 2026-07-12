# SQL Runtime Safety And Model Baseline

## Goal

Close the highest-risk SQL execution gaps and make model generation failures explicit instead of returning a successful analysis response with empty SQL. Restore deterministic backend verification before rebuilding the evaluation baseline.

## Scope

- Enforce a hard row limit and block unsafe PostgreSQL functions in SQL Guard.
- Execute Agent SQL in an explicit read-only transaction with statement and lock timeouts.
- Keep raw database errors in diagnostics while returning only category-level user errors.
- Return a service-unavailable API error when the analysis graph cannot produce executable SQL.
- Make API integration tests independent from the local model runtime.
- Update API/error/workflow documentation and run focused, full backend, frontend-build, and evaluation verification where available.

## Out Of Scope

- Creating or migrating a production PostgreSQL runtime role.
- Reintroducing fixed SQL templates.
- Expanding QuerySpec, business metric coverage, or frontend product pages.
- Adding CI, dependency locking, or a separate test database in this slice.

## Implementation Steps

- [x] Add runtime SQL limits and timeout configuration.
- [x] Clamp existing LIMIT values and block unsafe SQL functions.
- [x] Run guarded SQL in a read-only, time-bounded transaction and redact user-facing database errors.
- [x] Surface generated-SQL failure as a typed API service error.
- [x] Stabilize API tests with a deterministic model adapter seam.
- [x] Update API/workflow documentation.
- [x] Run validation and record the current evaluation baseline or its blocker.

## Validation Plan

- Focused Guard and Executor tests, including oversized LIMIT, blocked sleep, timeout setup, and error redaction.
- API tests for successful analysis through a deterministic adapter and unavailable model behavior.
- `npm.cmd run backend:test`.
- `npm.cmd run frontend:build`.
- `npm.cmd run eval:standard` when the local model service is available; otherwise record the exact failure.

## Risks

- Existing runtime connections use an administrative local database account; application-side read-only transactions reduce but do not replace a dedicated least-privilege role.
- The current local model may be unavailable or produce semantically invalid SQL, so live evaluation remains an external dependency.
- Existing tests and SQL Memory records may rely on legacy template behavior and need explicit, deterministic test seams.
