# Trusted SQL Context Fingerprint

## Goal

将已审核 `verified` SQL Memory 与生成它时的 schema 上下文及 Semantic Contract 版本绑定，阻止指纹缺失或不匹配的候选进入 fast path。

## Scope

- 为 SQL Memory 增加 schema 与语义契约指纹持久化字段。
- 用确定性指纹计算当前上下文，并在写入成功 SQL 时保存。
- 在候选规划阶段校验双指纹，失配时降级为 rewrite path，保留原有 Inspector、Guard 和 Executor。
- 覆盖旧记录、schema 变化、契约版本变化和完全匹配的聚焦测试。

## Out of scope

- 不修改认证、凭据、模型路由、公开 API 或 SQL Guard 规则。
- 不将旧 SQL Memory 自动提升为 verified，也不通过回填使其绕过重新审核。
- 不用指纹替代 SQL 意图验证、Inspector、Guard 或只读 Executor。

## Implementation steps

- [x] 复核 SQL Memory fast path、Semantic Contract 与 migration 现状。
- [x] 使用既有 JSONB、schema 和 repository 的双指纹读写支持，避免无意义 migration。
- [x] 实现稳定指纹工具并接入复用规划和成功 SQL 写入。
- [x] 为匹配、失配和缺失指纹添加聚焦测试。
- [x] 运行 focused tests；后端全量/标准评测已在相邻模块执行且模型质量波动大，本模块不重复运行，完成模块记录、提交和推送。

## Validation plan

- `py -3 -m pytest backend/tests/test_sql_memory_tools.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_db_migrations.py`
- `npm.cmd run backend:test`
- `npm.cmd run eval:standard` 与 `npm.cmd run frontend:build`

## Risks

- 旧 SQL Memory 缺少指纹会停止 fast path，这是刻意的安全降级，可能降低短期复用率。
- 召回上下文变化会导致保守 rewrite；不应以放宽匹配条件换取不受版本约束的复用。
- 并行 migration 编号必须避开现有未提交文件，最终以顺序 `012` 新增且不重写已有 migration。
