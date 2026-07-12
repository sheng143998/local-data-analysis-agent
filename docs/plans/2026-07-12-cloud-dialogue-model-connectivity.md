# Cloud Dialogue Model Connectivity

## Goal

Restore the configured cloud dialogue model so complete questions use model-first semantic understanding and clarification follow-ups are generated from the active conversation instead of an obsolete fixed fallback message.

## Scope

- Prevent the configured Alibaba Cloud-compatible intent provider from inheriting an unusable local SOCKS proxy.
- Replace the fixed generic clarification fallback with a neutral missing-information prompt for model-unavailable cases.
- Let a user request to modify a pending question use the model's current contextual clarification instead of replaying the old question.
- Add transport, parser, and follow-up regression tests.

## Out Of Scope

- Expose, commit, rotate, or display cloud credentials.
- Route SQL generation through the dialogue model or bypass SQL safety validation.
- Change the database schema or add a fixed SQL response for user totals.

## Implementation Steps

- [x] Diagnose the live intent-parser response and identify the SOCKS proxy dependency error.
- [x] Add explicit provider transport behavior for Alibaba Cloud-compatible model calls.
- [x] Replace obsolete fallback wording and preserve model-provided follow-up clarification.
- [x] Add focused regression coverage.
- [x] Verify a real cloud intent call, run backend tests and frontend build.
- [x] Record the completed module and remaining network risks.

## Validation Plan

- Call the configured intent parser for `当前用户总数是多少？` and verify it returns `source=llm` without the SOCKS proxy warning.
- Verify a modification request uses a newly parsed clarification instead of the prior clarification text.
- Run focused tests, `npm.cmd run backend:test`, and `npm.cmd run frontend:build`.

## Risks

- Some cloud deployments intentionally require a proxy. Provider-specific direct transport must be explicit and limited to the configured Alibaba Cloud provider.
- Cloud model output can still be invalid or ambiguous; parser validation and SQL safety boundaries remain mandatory.
