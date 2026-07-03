# SQL Guard / Validator 计划

Goal: 为后续模型生成 SQL 建立确定性的安全校验和基础质量校验，确保 SQL 不能绕过 Guard 直接执行。

当前正在做：模块已完成，SQL Guard / Validator 已实现并通过验证。

Scope:
- 包含：Pydantic 输入输出、`sqlglot` 解析、Validator、Guard、单元测试、文档和 handoff 更新。
- 不包含：真实 SQL Executor、LLM repair、动态 schema metadata 检索。

Module boundary:
- Upstream inputs: 模型或模板生成的 SQL 文本、允许访问的数据表、行数限制。
- Downstream outputs: 校验结果、安全 SQL、错误/警告。
- Likely touched files: `backend/app/schemas`, `backend/app/tools`, `backend/tests`, `backend/requirements.txt`, `docs/`。

Business logic:
- 用户问题最终会转 SQL，但 SQL 必须先经过 Validator 和 Guard。
- Guard 只允许 SELECT、禁止多语句、禁止写操作、禁止非白名单表，并自动补 LIMIT。
- Validator 负责质量规则，比如 `SELECT *`、空 SQL、语法错误、缺少 LIMIT 等。

Data contract:
- `SqlValidationRequest`: `sql`, `allowed_tables`, `max_rows`
- `SqlValidationResult`: `is_valid`, `errors`, `warnings`, `tables`, `normalized_sql`
- `SqlGuardResult`: `allowed`, `final_sql`, `errors`, `warnings`

Implementation steps:
- [x] 创建模块计划
- [x] 添加依赖和 Pydantic schema
- [x] 实现 SQL Validator
- [x] 实现 SQL Guard
- [x] 添加单元测试
- [x] 运行验证
- [x] 更新 handoff 和模块文档
- [x] commit 并 push

Validation plan:
- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

Risks and open questions:
- V1 先用静态白名单表；后续应接入 `schema_metadata`。
- `sqlglot` 可解析多方言，但 V1 仅按 PostgreSQL 目标校验。
