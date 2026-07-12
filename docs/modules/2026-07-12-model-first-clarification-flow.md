# Model First Clarification Flow

## Completed Behavior

- A successful intent-model response with a natural-language metric candidate now proceeds to retrieval and SQL generation when the model says clarification is unnecessary, even when the candidate is absent from the predefined metric catalog or has a low confidence score.
- A model candidate is no longer overwritten by a weaker heuristic match. This prevents questions such as `当前用户总数是多少？` from being reduced to a generic user dimension and then forced into clarification.
- The prompt now requires the intent model to ask only for information that materially changes the query and to write its own clarification based on the user's wording. Predefined catalog misses alone are not a reason to ask for confirmation.
- A follow-up that rejects the prior recommendation, such as `我不想查询这些`, is treated as a rejection of the suggestion rather than cancellation of the original request. The original question is sent back to the intent model with bounded conversation context.
- The chat page renders a response summary only once; the duplicate natural-language analysis panel was removed.

## Model Boundary

- `INTENT_MODEL_*` is the dedicated dialogue-semantic configuration. It may point to a cloud OpenAI-compatible model for question understanding and natural clarification.
- `MODEL_*` remains the SQL-generation configuration. A dialogue model never directly executes SQL; all SQL still passes QuerySpec validation, SQL Guard, and the read-only executor.
- No API key, endpoint, or local environment value is committed. Cloud settings remain developer-local in `backend/.env`.

## API And Data Contract Impact

- No public route or response schema changed.
- Internal `ParsedQuestionIntent.semantic_metrics` and `semantic_dimensions` are preserved through follow-up completion so the downstream SQL generator receives the original semantic requirement.

## Validation

- Focused: `.venv\\Scripts\\python -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_conversation_service.py backend/tests/test_analysis_graph_sql_selection.py` -> `52 passed, 1 warning`.
- Backend: `npm.cmd run backend:test` -> `214 passed, 1 warning`.
- Frontend: `npm.cmd run frontend:build` -> passed.
- Standard evaluation was invoked, but the current local `AUTH_REQUIRED=true` configuration makes its unauthenticated TestClient calls return `401` for all cases. The generated `0/20` report was discarded and the prior report restored; this run is not a semantic or SQL-quality measurement.

## Remaining Risks And Follow-up

- Effective conversational quality requires a working cloud or local `INTENT_MODEL_*` provider. If that provider is unavailable, the conservative heuristic fallback may still ask for clarification on unknown business concepts.
- The standard evaluation runner should obtain a test session or explicitly use an isolated authentication-disabled test configuration before it can validate this authenticated local environment.
- The configured SQL model still determines whether an understood but non-predefined concept can produce executable SQL. It remains subject to existing safety checks and may return a safe failure rather than an answer.
