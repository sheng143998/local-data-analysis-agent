# Frontend Dev Server Port

## Completed

- Changed the Vite development command from `0.0.0.0:5173` to `127.0.0.1:3000`.
- Changed preview binding to `127.0.0.1` so local preview does not expose all interfaces by default.
- Added `localhost:3000` and `127.0.0.1:3000` to default FastAPI CORS origins while retaining legacy 5173 origins for explicit custom configurations.

## Root Cause

Windows reserved TCP ports `5139-5238` on this machine. Vite's old `0.0.0.0:5173` binding fell inside that excluded range and failed with `EACCES`.

## Validation

- Vite starts and listens on `127.0.0.1:3000`.
- Local HTTP request to `http://127.0.0.1:3000/` succeeds.
- `npm.cmd run frontend:build` passes.

## Notes

- The development server is intentionally bound to loopback only. Use an explicit, separately reviewed configuration for LAN access.
