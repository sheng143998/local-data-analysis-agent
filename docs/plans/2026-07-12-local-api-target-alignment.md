# Local API Target Alignment

## Goal

Make the local frontend call the backend instance that is actually running, so authentication requests can complete during local integration.

## Scope

- Verify the local frontend API base URL and active backend listener.
- Align the ignored local frontend environment configuration with the active backend port.
- Restart the frontend development server and verify health, CORS preflight, and authentication endpoint reachability.

## Out Of Scope

- Change authentication business logic, account data, or backend API contracts.
- Change committed default production networking configuration.
- Commit local environment values.

## Implementation Steps

- [x] Confirm that the active backend listens on port 8000 while the frontend targets port 8002.
- [x] Update the ignored local frontend API base URL to port 8000.
- [x] Restart the frontend development server so Vite reloads the environment configuration.
- [x] Verify frontend availability, backend health, and credentialed CORS preflight.
- [x] Record the completed local integration fix.

## Validation Plan

- Request `http://127.0.0.1:3000` after the Vite restart.
- Request `http://127.0.0.1:8000/api/health`.
- Send an `OPTIONS /api/auth/login` request from `http://127.0.0.1:3000` and verify credentialed CORS headers.
- Run `npm.cmd run frontend:build`.

## Risks

- The ignored local configuration deliberately varies by developer; a later switch of the backend port requires restarting Vite and aligning this value again.
- This check proves transport connectivity only; invalid account credentials must remain a normal authentication error.
