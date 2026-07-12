# QuerySpec Semantic Contract

## Goal

Introduce one structured query-semantic contract that represents metrics, dimensions, time range, ranking, required table groups, expected output aliases, and forbidden semantics. Use it to stop user, funnel, and coupon questions from falling into generic clarification and to keep SQL generation, validation, and SQL Memory aligned.

## Scope

- Add a typed QuerySpec schema and deterministic builder.
- Extend intent recognition for new users, ordering users, user purchase ranking, funnel conversion, coupon redemption, coupon AOV comparison, and traffic-source conversion.
- Include QuerySpec in the model SQL prompt.
- Drive generated SQL and Memory verification from QuerySpec requirements.
- Store actual SQL tables and QuerySpec metrics/dimensions in SQL Memory.
- Add focused coverage and rerun standard evaluation.

## Out Of Scope

- Add fixed SQL templates for the new business questions.
- Change database tables or create new metric-definition records.
- Replace the standard evaluator's string assertions with full AST/result assertions.
- Build a frontend QuerySpec/debug view.

## Implementation Steps

- [x] Define QuerySpec schema, semantic mappings, table groups, aliases, and forbidden semantics.
- [x] Attach QuerySpec to intent parsing and prevent recognized business questions from falling into generic clarification.
- [x] Include QuerySpec in SQL generator payloads.
- [x] Use QuerySpec in SQL intent validation and SQL Memory verification/update.
- [x] Add focused tests for new intent classes, validation, prompt payload, and Memory metadata.
- [x] Run backend tests, frontend build, standard evaluation, and document the new baseline.

## Validation Plan

- Parser tests for every new metric family and expected table group.
- Graph tests that reject missing QuerySpec tables/aliases and accept valid alternatives.
- Prompt-payload tests proving QuerySpec reaches the model.
- Memory-update test proving actual SQL tables and semantic dimensions are persisted.
- `npm.cmd run backend:test`, `npm.cmd run frontend:build`, and `npm.cmd run eval:standard`.

## Risks

- The local model may remain unable to synthesize valid SQL for all new semantic contracts; QuerySpec improves grounding and validation but does not replace model capability.
- Some metrics permit equivalent SQL forms, so requirements should use table groups and alias families rather than a single literal SQL shape.
- Existing SQL Memory entries contain legacy metadata and will improve only after successful queries are written with the new contract.
