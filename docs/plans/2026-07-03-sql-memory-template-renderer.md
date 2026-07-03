# SQL Memory 参数化模板与时间范围改写计划

## Goal

让 SQL Memory 不只复用完全固定 SQL，而是能从用户问题中解析“最近 7 天 / 30 天 / 90 天”等时间范围，并渲染到销售趋势 SQL 模板中，为 `fast_path` 参数化复用和后续 Rewriter 打基础。

## 当前正在做

当前正在做：SQL Memory 参数化模板与时间范围改写已完成，已提交并推送。

## Scope

包含：

- 新增时间范围解析工具。
- 新增销售趋势 SQL 模板渲染工具。
- 将 SQL Memory 的 `parameters` 写入 `days`。
- 让 `fast_path` 命中时也可以按当前问题重新渲染时间范围。
- 补充 focused backend tests。
- 更新 README、模块完成文档和 handoff。

不包含：

- 复杂多维过滤条件渲染。
- 品类、城市、Top N 等参数化。
- LLM SQL Rewriter / Generator。
- 前端开发者调试页。

## Module Boundary

- 上游输入：用户自然语言问题、SQL Memory 候选。
- 下游输出：带 `days` 参数的 SQL、`sql_memories.parameters`、`query_runs.final_sql`。
- 可能触达文件：
  - `backend/app/tools/sql_template_tools.py`
  - `backend/app/tools/sql_memory_tools.py`
  - `backend/app/db/repositories/memory_repository.py`
  - `backend/app/schemas/memories.py`
  - `backend/app/agents/analysis_graph.py`
  - `backend/tests/test_sql_template_tools.py`
  - `backend/tests/test_sql_memory_tools.py`
  - `README.md`
  - `docs/modules/2026-07-03-sql-memory-template-renderer.md`
  - `docs/handoff/current.md`

## Business Logic

用户问“最近 7 天销售额是多少？”或“最近 30 天销售额按天变化如何？”时，系统应识别时间范围，并把它作为可审计参数写入 SQL Memory。当前最小实现先通过 `LIMIT N` 表示最近 N 个有交易日期，后续可升级为基于数据日期范围的严格日历窗口。

## Data Contract

- `SalesTrendParameters`
  - `days`
  - `granularity`
- `SqlMemoryUpsert.parameters`
  - `{"days": 30, "granularity": "day"}`
- `SqlReusePlan.selected_sql`
  - 当前问题渲染后的最终 SQL。

## Implementation Steps

任务清单：

- [x] 读取 handoff、草案和当前 SQL Memory 实现。
- [x] 创建本计划文档。
- [x] 实现时间范围解析和模板渲染工具。
- [x] 接入 analyze 和 SQL Memory 写入。
- [x] 补充测试、README、模块文档和 handoff。
- [x] 运行验证。
- [x] commit 并 push。

## Validation Plan

- `npm run backend:test`：已通过，28 个测试通过。
- `npm run test:e2e`：已通过，FastAPI smoke 闭环通过。
- `npm run frontend:build`：已通过，Vite production build 成功。

## Risks and Open Questions

- 当前用最近 N 个有交易日期表达“最近 N 天”，不是严格自然日窗口。
- 后续需要支持品类、城市、Top N、按月等更多参数。
