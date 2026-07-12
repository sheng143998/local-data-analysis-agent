# Current Aggregate SQL Repair

## Completed Behavior

- The intent prompt now treats `当前` and `目前` as a current-state snapshot, not an implicit date, new-user, order, payment, or success filter.
- The SQL generation payload now requires the model to count an entity table's distinct primary key for an entity-total question, rather than translating it into a different business measure.
- The payload explicitly forbids `orders.status = 'paid'`. A payment-status filter is permitted only when the user requests a paid or successful scope and must use the `payments` relationship.
- The Repair Prompt now gives an executable correction for the payment-status Guard error: remove an unrequested payment condition, or join `payments` correctly when that condition is explicitly required.

## Root Cause

The failed run for `当前用户总数是多少` first classified the request as new/ordering-user metrics and then generated an invalid `orders.status = 'paid'` predicate. The model repeated the predicate after one repair attempt. SQL Guard correctly blocked execution and the API returned `503` instead of executing an invalid business query.

## API And Safety Impact

- No public API contract changed.
- No fixed user-count SQL or new SQL bypass was added.
- QuerySpec validation, SQL Guard, and read-only execution remain mandatory and were responsible for safely rejecting the failed run.

## Validation

- Focused: `.venv\\Scripts\\python -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py` -> `57 passed`.
- Live read-only retry for `当前用户总数是多少？` generated `SELECT COUNT(DISTINCT users.id) AS user_count FROM users LIMIT 30`, passed SQL Guard, and returned `99441`.
- Backend: `npm.cmd run backend:test` -> `219 passed, 1 warning`.
- Frontend: `npm.cmd run frontend:build` -> passed.
- Standard evaluation remains excluded because its unauthenticated TestClient is incompatible with the current `AUTH_REQUIRED=true` local configuration.

## Remaining Risks And Follow-up

- The local 3B SQL model can still vary between requests. The Prompt and Repair improvements reduce one observed failure mode but do not substitute for a stronger SQL model or a broader authenticated evaluation suite.
- The generic presenter labels this user-total result as a sales trend. Result presentation should later use the selected semantic metric and result columns to produce an accurate user-total summary.
