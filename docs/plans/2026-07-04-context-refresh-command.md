# 数据上下文刷新命令计划

## Goal

换库、导入新表或调整字段后，开发者不应该靠记忆手动依次执行 schema 同步和 embedding 同步。本模块新增一个统一的数据上下文刷新入口，把 `schema_metadata` 同步和 schema/metric/SQL Memory embedding 同步串联起来，提升换表后的检索资产刷新效率。

## Current task

当前正在做：数据上下文刷新命令已完成实现、文档、验证、commit 和 push。

## Scope

包含：

- 新增后端服务，先同步真实 PostgreSQL `public` schema 到 `schema_metadata`。
- 可选同步 embedding，默认同步 schema、metric、memory。
- CLI 支持跳过 embedding，以及选择 embedding target。
- 增加 focused tests，验证调用顺序、跳过选项和目标选择。
- 更新 README、handoff 和模块完成说明。

不包含：

- 不新增固定 SQL 模板。
- 不改变普通用户前端。
- 不改变 `/api/analyze` 响应字段或主链路。
- 不改变数据库 migration。

## Module boundary

上游输入：

- PostgreSQL 当前 `public` schema。
- `metric_definitions` 和 `sql_memories` 中已有记录。
- CLI 参数。

下游输出：

- `schema_metadata` 最新字段结构。
- `schema_metadata.embedding`、`metric_definitions.embedding`、`sql_memories.question_embedding`、`sql_memories.sql_embedding`。
- CLI 输出刷新摘要。

预计触达文件：

- `backend/app/services/context_refresh_service.py`
- `backend/scripts/refresh_context.py`
- `backend/tests/test_context_refresh_service.py`
- `README.md`
- `docs/handoff/current.md`
- `docs/modules/2026-07-04-context-refresh-command.md`

## Business logic

当数据表发生变化时，系统需要先知道“有哪些表和字段”，再为这些上下文生成向量，后续检索和模型 SQL 生成才能尽量基于真实结构工作。该模块把这个刷新过程封装成一个命令，降低人工漏步骤风险。

## Data contract

不新增 API 字段。内部服务返回：

- `ContextRefreshResult.schema_result`
- `ContextRefreshResult.embedding_results`

## Implementation steps

- [x] 读取 handoff 和现有 schema/embedding 同步脚本。
- [x] 新增 context refresh 服务和 CLI。
- [x] 增加 focused tests。
- [x] 更新 README、handoff 和模块完成说明。
- [x] 运行验证。
- [x] commit 并 push。

## Validation plan

- `py -3 -m pytest backend/tests/test_context_refresh_service.py`，4 passed
- `npm run backend:test`，115 passed，1 个 `StarletteDeprecationWarning`
- `npm run frontend:build`，通过
- `npm run test:e2e`，通过，1 个 `StarletteDeprecationWarning`
- `py -3 backend/scripts/refresh_context.py --help`，通过
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%

## Risks and open questions

- embedding 同步仍依赖当前 `EMBEDDING_PROVIDER` 配置；本地默认 deterministic fallback 可跑通，但真实语义质量取决于真实 embedding provider。
- 本模块只做手动刷新命令，不做数据库变更监听或定时任务。
