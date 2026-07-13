# Semantic Contract 数据基础层

## Completed behavior

- 新增 `008_semantic_contracts.sql`，以 `contract_key + version` 唯一约束保存版本化指标、维度、实体和关系业务定义。
- 契约保存来源表字段、同义表达、默认过滤、时间粒度、聚合方式与扩展语义配置，但不保存或执行 SQL。
- 新增 `SemanticContractRepository`：默认读取最新启用版本、按类型列出启用契约、只新增版本而不覆盖既有口径。
- 新增 Pydantic 数据契约和无数据库依赖的 repository 聚焦测试。

## Key decisions

- 既有 `metric_definitions` 保持不变；Semantic Contract 是后续开放式 Resolver 的统一业务定义来源，迁移期间两者并存。
- 允许保存多个启用历史版本，默认读取同一键的最高启用版本，保证回滚时可通过状态切换恢复旧版本。
- 本模块不接入 Graph，且不改变 QuerySpec、SQL Guard 和只读 Executor 的安全边界。

## API and data-contract impact

- 新增内部表 `semantic_contracts`、schema `backend.app.schemas.semantic_contracts`、repository `SemanticContractRepository`。
- 未新增 API、前端类型或外部接口。

## Validation

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_semantic_contracts.py backend/tests/test_db_migrations.py`：`9 passed`。
- `py -3 -m pytest ...`：系统 Python 缺少 `langgraph`，在加载测试 `conftest.py` 时失败；已改用项目虚拟环境。
- `npm.cmd run backend:test`：`228 passed, 1 warning`。
- `.venv\\Scripts\\python backend/scripts/init_db.py`：真实 PostgreSQL 已成功应用 `008_semantic_contracts.sql`。

## Remaining risks and follow-up

- 后续 Semantic Resolver 接入前应补充版本状态迁移服务和预置、审查过的业务契约数据。
- 本子模块按主线并行协作约定不单独提交或推送，提交由主线统一完成。
