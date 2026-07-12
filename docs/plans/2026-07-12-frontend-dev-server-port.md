# Frontend Dev Server Port

## Goal

Make the frontend development server start reliably on Windows hosts where Vite's default port is reserved, while preserving local backend API access.

## Scope

- Bind Vite development and preview servers to the loopback address.
- Move the development server from excluded port `5173` to `3000`.
- Add the new development origin to default backend CORS settings.

## Out Of Scope

- Change production deployment networking.
- Add frontend API proxying or authentication.
- Modify Windows port-exclusion policy.

## Implementation Steps

- [x] Update frontend development and preview scripts.
- [x] Update backend default CORS origins.
- [x] Start Vite and verify that the selected address and port respond.
- [x] Run frontend production build and document the result.

## Validation Plan

- Run the frontend development script and request the local URL.
- Run `npm.cmd run frontend:build`.

## Risks

- Other local tools can still occupy port `3000`; Vite will report an address-in-use error instead of this Windows permission denial.
- A non-default CORS configuration must include the chosen development origin explicitly.
