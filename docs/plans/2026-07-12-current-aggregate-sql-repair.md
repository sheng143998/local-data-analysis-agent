# Current Aggregate SQL Repair

## Goal

Reduce safe `503` failures for complete current-state aggregate questions by carrying the intended entity-total semantics into SQL generation and by giving the repair prompt an executable response to invalid payment-status filters.

## Scope

- Clarify in the intent prompt that current-state wording is not itself a date range and does not imply new-user, ordering-user, or paid-order semantics.
- Add generic SQL generation requirements for entity totals and explicit payment filters.
- Add repair rules for invalid `orders.status = 'paid'` output.
- Add focused prompt and repair regression coverage.

## Out Of Scope

- Add a fixed `users` count SQL template or bypass the model SQL generator.
- Change the configured SQL model provider or send SQL-generation context to the cloud dialogue model.
- Relax QuerySpec validation, SQL Guard, or read-only execution.

## Implementation Steps

- [x] Update semantic and SQL generation prompt rules.
- [x] Add payment-filter-specific Repair Prompt instructions.
- [x] Add focused tests for current aggregate semantics and repair payloads.
- [x] Run focused/backend/frontend validation and record live retry evidence.

## Validation Plan

- Assert prompt payload distinguishes a current entity total from new-user, ordering-user, and paid-order metrics.
- Assert a payment-status guard error produces a repair instruction that removes an unrequested filter or joins `payments` correctly.
- Run focused pytest, backend tests, frontend build, and a read-only live analysis-graph retry.

## Risks

- A 3B SQL model can still produce unstable outputs. The change improves prompt and repair quality but cannot make stochastic model output deterministic.
- If a question explicitly requests paid or successful entities, the SQL must still use the valid `payments` relationship and remain subject to Guard.
