# Model First Clarification Flow

## Goal

Let a semantically complete user question proceed directly to retrieval and SQL generation, while asking a natural-language clarification only when the intent model identifies a material missing business requirement.

## Scope

- Make the intent parser treat model-provided semantic candidates as sufficient evidence to continue, even when they are not predefined metric IDs.
- Remove confidence-only clarification for successful model responses.
- Strengthen the intent prompt so the model asks only for genuinely missing information and writes the clarification itself.
- Resolve a rejection of a prior clarification as a return to the original question, rather than repeating the previous suggestion.
- Remove duplicate rendering of a clarification summary in the chat UI.
- Add focused tests for a complete unknown metric candidate, a genuinely vague question, and a rejected clarification suggestion.

## Out Of Scope

- Add a fixed SQL template for user totals or relax QuerySpec, SQL Guard, and read-only executor checks.
- Change the SQL model provider, model deployment, database schema, or account system.
- Add a separate clarification Agent or persist raw prompt data.

## Implementation Steps

- [x] Update intent-parser decision rules and prompt contract.
- [x] Update follow-up resolution to distinguish cancellation, rejection of a suggestion, and a meaningful supplement.
- [x] Prevent duplicate summary rendering for clarification responses.
- [x] Add parser, follow-up, service, and frontend regression coverage.
- [x] Run focused backend tests, frontend build, and standard evaluation.
- [x] Record completed behavior, validation, and remaining model-quality risks.

## Validation Plan

- Verify a model response with semantic metric candidate `当前用户总数` and `needs_clarification=false` enters the analysis graph.
- Verify `看看最近情况` still waits for clarification.
- Verify a rejection such as `我不想查询这些` does not repeat the old clarification and instead reparses the original question with the model.
- Run focused pytest, `npm.cmd run backend:test`, `npm.cmd run frontend:build`, and `npm.cmd run eval:standard`.

## Risks

- A local model can still misclassify an ambiguous question; SQL validation, Guard, and read-only execution remain mandatory after intent parsing.
- When the model service is unavailable, deterministic fallback remains intentionally conservative because it cannot safely infer arbitrary business semantics.
- Natural clarification quality depends on the configured intent model and must be measured with regression cases rather than assumed from prompt wording.
