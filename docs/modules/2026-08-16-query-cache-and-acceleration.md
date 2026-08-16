# 查询结果缓存与查询加速模块记录

## 完成内容

- 新增查询结果缓存配置：
  - `QUERY_CACHE_ENABLED`
  - `QUERY_CACHE_TTL_SECONDS`
  - `QUERY_CACHE_MAX_ENTRIES`
  - `QUERY_CACHE_PREFIX`
  - `QUERY_CACHE_SCHEMA_VERSION`
- 新增 `backend/app/services/cache_service.py`：
  - Redis 优先，Redis 不可用时降级为进程内 LRU。
  - 支持 `get` / `set` / `delete_prefix` / `clear_all`。
- 新增 `backend/app/services/cache_key_builder.py`：
  - 缓存 Key 绑定 SQL、Query Plan、用户 ID、语义合同版本和 schema 版本。
  - 使用稳定 SHA-256 摘要，避免不同权限/口径用户互相读到结果。
- 接入 `analysis_graph.py`：
  - `_explain_sql_node` 在 Guard 后先查缓存，命中时跳过 EXPLAIN 和数据库执行。
  - `_execute_sql_node` 在成功执行后写缓存。
  - Run Trace 的 tool_calls 增加 `cache_hit` 字段。
- 新增管理员缓存清理接口：
  - `POST /api/cache/clear`，仅 `admin` + CSRF 可调用。
- 缓存失效：
  - 指标创建/修改/删除后清空缓存。
  - Context Refresh（schema/embedding/合同刷新）后清空缓存。

## 关键决策

- 缓存只保存 `status == "success"` 的执行结果，不缓存 Guard 拒绝、EXPLAIN 失败或执行错误。
- 缓存 Key 包含用户 ID，避免后续行级权限引入后出现越权缓存读取。
- 先不做 L1/L2 两级缓存，直接使用 Redis 作为主缓存，本地内存作为降级。
- 缓存命中仍然走 Guard，但跳过 EXPLAIN 和数据库主查询。

## API / 数据契约影响

- 新增接口：`POST /api/cache/clear`。
- 不改数据库表结构。
- `tool_calls.output_payload` 新增 `cache_hit` 字段。

## 验证

- `backend/tests/test_cache_service.py`：`5 passed`。
- 相关 focused：
  - `backend/tests/test_metrics.py`
  - `backend/tests/test_context_refresh_service.py`
  - 合计 `10 passed`。
- `backend/tests/test_analysis_graph_sql_selection.py`：`38 passed`。
- `python -m compileall -q backend/app backend/tests/test_cache_service.py` 通过。
- `git diff --check` 通过（仅 LF/CRLF 提示）。
- 说明：全量后端测试在 180s 内未跑完，`test_api.py` 中 3 条真实模型链路用例返回 503，属于本地模型/环境问题，与本次缓存改动无关。

## 剩余风险

- 缓存失效依赖显式清空；如果 schema/合同通过其他路径变更，需要补清空钩子。
- 当前 `permission_hash` 直接用用户 ID，缓存命中率在多用户下会下降；后续可在行级权限稳定后改为权限范围哈希。
- Redis 不可用时进程内 LRU 只对本进程有效，多进程部署时缓存命中率下降。

## 提交

- Commit：`9f7a2c9`（`feat: add query result cache and acceleration`）。
- Push：已推送至 `origin/main`（`8ff4e6e..9f7a2c9`）。

## 后续工作

- Phase 2：并发控制。
- Phase 3：鉴权与数据隔离。
- Phase 4：飞书集成。
- 全量后端测试与标准 eval 在后续阶段统一回归。
