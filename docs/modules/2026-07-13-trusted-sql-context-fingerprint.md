# Trusted SQL Context Fingerprint

## Completed behavior

- SQL Memory 成功写入时会把 schema 与已解析语义契约的 SHA-256 指纹保存到既有 `filters.context_fingerprints` JSONB。
- Graph 在 Memory 检索时重新计算当前指纹。仅当 `verified`、分数、表匹配以及双指纹均匹配时才允许 fast path。
- 旧记录、指纹缺失和 schema/contract 版本失配都会降级为 rewrite path；后续仍由模型、Inspector、Guard 和只读 Executor 处理。

## Key decisions

- 不新增数据库列：`filters` 已是 SQL Memory 的受控扩展元数据（既有 trust status 也位于此处），避免新增未被查询使用的 schema 字段。
- 指纹输入是已召回的表、字段、关系及已绑定契约 key/version/source 元数据，不包含用户问题、SQL 正文、提示词或凭据。

## API and data-contract impact

- 无公开 API 变更。
- 内部 `SqlMemoryCandidate` 增加指纹匹配诊断，`SqlMemoryUpsert` 增加持久化 filters。

## Validation

- `.venv\\Scripts\\python -m pytest backend/tests/test_sql_memory_tools.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_memory_service.py`：`47 passed`。
- `git diff --check` 通过。
- 后端全量和标准评测未为该 metadata-only 模块重复运行；相邻模块的 full test 曾在 120 秒上限未完成，标准评测受本地模型输出波动影响，详见 handoff。

## Remaining risks and follow-up

- 首次上线的 legacy verified SQL 会因没有指纹而降级，这是一项刻意的安全保守策略。
- 指纹依赖召回上下文；后续可在管理员审核界面展示失配原因，帮助重新审核后再提升为 verified。
