---
name: local-data-analysis-development
description: Enforce the development workflow for this local data analysis Agent. Use for any code, API, database, frontend, evaluation, configuration, documentation, or refactoring change in this repository. Require reading and updating the handoff, creating a plan before code changes, maintaining UTF-8 Chinese text handling, validating changes, and recording completed work.
---

# Local Data Analysis Agent Development

Apply the repository workflow before making development changes. Treat the handoff as the current-state source of truth and preserve a plan, implementation record, validation evidence, and completion handoff update.

## Mandatory Workflow

### Before Development

1. Read `docs/handoff/current.md` using UTF-8 before inspecting or editing implementation files.
2. Inspect the working tree and relevant code, tests, contracts, migrations, and documentation. Preserve unrelated user changes.
3. Create `docs/plans/YYYY-MM-DD-<task-name>.md` before editing application code, configuration, migrations, API contracts, or tests.
4. Update `docs/handoff/current.md` before implementation. Record the task, scope, plan path, current risks, and intended validation.
5. Include `Goal`, `Scope`, `Out of scope`, `Implementation steps`, `Validation plan`, and `Risks` in every plan. Maintain implementation steps as a checklist.

### During Development

1. Keep layers explicit: routes in `backend/app/api/` stay thin; application orchestration belongs in `services/`; Agent graphs in `agents/`; deterministic capabilities in `tools/`; persistence in `db/repositories/`; contracts in backend `schemas/` and frontend `types/`.
2. For API changes, follow `docs/api_change_process.md`. Synchronize routes, Pydantic schemas, services, frontend clients, frontend types, tests, and affected `docs/api*.md` files.
3. For database schema changes, add a new migration. Never rewrite an applied migration. Synchronize repository code, schemas, scripts, and tests.
4. Preserve the SQL safety boundary: an LLM never executes SQL directly. Generated or reused SQL must pass intent validation, SQL Guard, and the read-only executor.
5. Keep secrets, connection strings, user data, prompts, tool payloads, vector scores, and raw internal errors out of commits and ordinary user-facing pages.
6. Read and write Chinese text files as UTF-8. Use `-Encoding utf8` for PowerShell reads. Do not rely on the shell's default encoding unless the file is known to require a different encoding.
7. 新增或修改的代码注释默认使用中文。注释必须说明业务目的、业务规则、安全边界或非显而易见的取舍；不得只复述语法或变量赋值。修改既有英文注释时，除外部协议或引用内容必须保留英文外，应同步改为简洁的中文业务注释。

### Before Completion

1. Run the validation promised by the plan. Report unavailable validation and its exact reason.
2. Create `docs/modules/YYYY-MM-DD-<task-name>.md`. Include completed behavior, key decisions, API/data-contract impact, validation commands and results, remaining risks, and follow-up work.
3. Update `docs/handoff/current.md` with the completed state, concise summary, validation, risks, and next steps. Keep detailed implementation facts in the module document rather than duplicating them in the handoff.
4. Update the plan checklist to match what actually happened before reporting completion.
5. Treat every independently testable, completed module as one delivery unit. After its promised validation passes, inspect `git status`, stage only the files belonging to that module, create a concise commit, and push the current branch to its configured remote before starting the next module. Do not include unrelated user changes; if they cannot be separated safely, report the conflict instead of silently committing them.
6. Record the commit hash and push result in the module record and handoff. A failed push means the module is not fully delivered; keep working to resolve it or report the exact blocker.

## Validation Baseline

| Change | Minimum validation |
| --- | --- |
| Frontend component, page, type, or API client | `npm.cmd run frontend:build` |
| Backend Python logic, route, schema, or repository | Focused pytest; run `npm.cmd run backend:test` when available |
| Analyze workflow, retrieval, SQL Memory, SQL generation, Guard, executor, or presenter | Focused tests plus `npm.cmd run eval:standard` |
| API contract | Backend tests, frontend build, relevant smoke test, synchronized API documentation |
| Migration or metadata sync | Migration and repository verification; small-batch sync verification when relevant |
| Documentation only | Verify paths, links, commands, and descriptions against the repository |

## Documentation Boundaries

Use these files for their intended purpose:

- `docs/handoff/current.md`: current state, risks, next steps, and pointers.
- `docs/plans/`: development plans created before implementation.
- `docs/modules/`: completed-module records and validation evidence.
- `docs/api*.md`: API contracts, mappings, errors, and change process.
- `docs/agent_workflow.md`: retrieval, SQL generation, safety, and observability boundaries.

## Exceptions

- For read-only analysis, questions, or requests explicitly forbidding file changes, do not create plan or completion documents. Still read the handoff whenever project state is relevant.
- For urgent fixes, create the smallest viable plan and handoff update before implementation. Do not retroactively represent a plan as pre-work.
- If the user explicitly directs skipping documentation, record the exception and reason in the final response or task record. Do not fabricate validation or documentation.
- If the user explicitly asks to defer a commit or push, record that decision in the handoff. Otherwise, the verified-module commit and push rule is mandatory.
