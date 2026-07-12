# Cloud Dialogue Model Connectivity

## Completed Behavior

- The configured Alibaba Cloud-compatible intent provider now uses a direct HTTP transport and does not inherit the local SOCKS proxy environment.
- The runtime no longer fails with the missing `socksio` proxy dependency and fall back to the obsolete business-overview clarification.
- The local intent-model request budget is configured as one 45-second attempt. This matches the observed cloud response latency and avoids two short failed attempts.
- When the cloud model supplies a clarification response without metric candidates, the parser keeps that response instead of replacing it with a heuristic clarification.
- A follow-up such as `我想修改` updates the pending clarification with the cloud model's context-aware question.
- If the model is genuinely unavailable, the deterministic fallback is neutral and asks for the missing business object or metric. It no longer recommends a fixed sales/order/customer-price bundle.

## Root Cause

The cloud intent configuration was present, but `HttpxChatTransport` inherited the local SOCKS proxy for the `aliyun` provider. The Python environment did not include `socksio`, so every cloud call failed before reaching the provider. The parser then correctly applied its conservative fallback, but that fallback still contained the obsolete fixed clarification text.

## Model And Safety Boundary

- `INTENT_MODEL_*` remains limited to dialogue semantic understanding and clarification.
- `MODEL_*`, QuerySpec validation, SQL Guard, and the read-only executor remain the SQL execution boundary.
- No cloud credential, proxy value, or local environment content is recorded in this document or committed.

## Validation

- Focused: `.venv\\Scripts\\python -m pytest backend/tests/test_model_adapter.py backend/tests/test_question_intent_parser.py backend/tests/test_conversation_service.py` -> `29 passed, 1 warning`.
- Real configured cloud call for `当前用户总数是多少？` returned `source=llm`, confidence `0.85`, `needs_clarification=false`, and semantic user-total candidates.
- Real configured cloud follow-up for `我想修改` returned `source=llm`, `needs_clarification=true`, and a context-aware clarification asking what the user wants to change.
- Backend: `npm.cmd run backend:test` -> `217 passed, 1 warning`.
- Frontend: `npm.cmd run frontend:build` -> passed.

## Remaining Risks And Follow-up

- Cloud calls can take tens of seconds. The current single 45-second attempt favors a successful natural response over a fast retry; later work may add streamed status updates or a latency budget configurable per environment.
- The authenticated local standard evaluation runner still needs a test session before it can validate end-to-end SQL quality under `AUTH_REQUIRED=true`.
