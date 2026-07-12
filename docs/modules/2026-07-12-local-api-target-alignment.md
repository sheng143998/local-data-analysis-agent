# Local API Target Alignment

## Completed Behavior

- The ignored local frontend environment configuration now targets `http://127.0.0.1:8000`, matching the backend instance currently started by the developer.
- Vite was restarted on `http://127.0.0.1:3000` so the updated environment value is loaded into the browser bundle.
- The local environment file remains ignored and is not included in version control.

## Root Cause

The frontend had retained a local API base URL for port `8002`, while the active backend listened only on port `8000`. The browser therefore failed before authentication logic could process the login request and displayed the generic local-service error.

## API And Data Contract Impact

- No API route, authentication contract, account record, or backend configuration changed.
- Only the developer-local frontend API target changed from port `8002` to port `8000`.

## Validation

- `http://127.0.0.1:3000` returns HTTP 200 after the Vite restart.
- `http://127.0.0.1:8000/api/health` returns a healthy response.
- `OPTIONS http://127.0.0.1:8000/api/auth/login` from origin `http://127.0.0.1:3000` returns HTTP 200 with the matching allow-origin header and credential support.
- `npm.cmd run frontend:build` passes, and the generated bundle contains the local port `8000` API target.

## Remaining Risks And Follow-up

- The local API target is intentionally developer-specific. When the backend port changes, update `frontend/.env.local` and restart Vite before testing.
- This repair does not validate a particular account password; authentication failures with a reachable service should be shown as credential errors rather than connectivity errors.
