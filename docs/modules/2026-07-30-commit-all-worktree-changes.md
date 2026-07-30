# 工作区全部改动提交交付

## 完成行为

- SQL Memory 增加稳定成功计数、自动 verified 晋级、失败降级、归一化问题唯一约束和并发安全 upsert。
- AgentService 在完整路由前增加已验证记忆精确命中快路径；复用 SQL 仍经过 Guard、EXPLAIN 和只读执行，失败时降级并回退主管线。
- 意图解析与 embedding/schema/metric 预取可并行执行，问题向量和预取上下文在图内复用。
- 查询运行日志与 SQL Memory 写回支持有界线程池异步簿记，响应携带对应 `run_id`。
- Embedding 与低基数 Schema 样本值增加进程内缓存；Repair payload 只保留相关表上下文。
- migration `017` 增加 SQL Memory 唯一索引、热点查询索引和 pgvector HNSW 索引，并提交过期数据清理脚本。
- 新增第二轮编排与记忆生命周期测试，修复共享 API fixture 对归一化日销售趋势问题的匹配。
- 提交第二轮优化实施计划、项目精通与面试准备指南，并删除两个旧一键批处理脚本。

## 关键决策

- fast path 只接受归一化问题精确匹配且 `trust_status=verified` 的 SQL；相似问题仍进入完整链路。
- 记忆复用不会绕过实时 Schema 校验、安全 Guard、EXPLAIN 或只读事务。
- 后台簿记异常只写日志，不反向破坏已经完成的用户响应；测试可关闭异步以保持确定性。
- 检索预取失败时回退图内串行检索，意图解析失败仍按原有边界处理。
- migration `017` 在建立唯一索引前按归一化问题去重并保留最新记录。

## API 与数据契约影响

- `AnalyzeResponse` 增加并贯通 `run_id`，调用方可直接关联 `/api/runs/{run_id}`。
- Retrieval Schema 字段增加真实样本值载荷，供 SQL 生成约束枚举取值。
- SQL Memory 表新增生命周期字段/约束与索引依赖；本地数据库已应用 migration `017`。
- `.env.example` 增加 memory-first、异步簿记、自动可信阈值、缓存、并行预取和样本数量开关。

## 验证结果

- `.venv\\Scripts\\python backend\\scripts\\init_db.py`：migration `017` 应用成功。
- focused pytest：`52 passed, 1 warning`。
- `npm.cmd run frontend:build`：通过；保留现有单 chunk 大于 500 kB 警告。
- `npm.cmd run eval:standard`：进程在 300 秒上限未退出，但在超时前写出完整 20-case 报告；`19/20` 执行成功且严格通过，`dataset.is_complete_dataset=true`。
- `npm.cmd run backend:test`：两次分别在 180 秒和 300 秒上限未结束，没有形成全量通过/失败汇总；不能记为通过。
- `npm.cmd run test:e2e`：本机鉴权开启，旧 smoke 未登录，返回 `401`；单次环境变量覆盖被配置加载顺序覆盖，仍未通过。
- `cleanup_data.py --dry-run`、Python `compileall` 和 `git diff --check`：通过。
- 敏感信息扫描未发现 API Key、私钥或真实密钥；`.env.example` 只有占位项和布尔/数值开关。

## 剩余风险

- 全量 pytest 存在长时间不退出问题，需要使用 `-vv`、分组或超时插件定位具体阻塞用例。
- E2E smoke 需要按当前鉴权契约先登录，或显式提供独立的无鉴权测试 Settings 注入方式。
- 标准评测已完成报告写入但进程未退出，可能与后台线程或资源关闭有关，需要单独定位。
- migration `017` 会删除同一 `normalized_question` 的旧重复记录，只保留最新记录；生产应用前应备份并评估重复数据。

## 后续工作

- 定位 pytest 和 Eval Runner 的进程退出阻塞。
- 更新 `backend/tests/smoke_api.py`，使其使用测试认证账号或显式测试配置。
- 对 HNSW 索引和缓存命中率补充真实数据规模下的性能对照。

## Git 交付

- 主提交：`6d91afe`（`完成第二轮 Agent 编排与记忆优化`）。
- 初次推送发现远端新增两个批处理脚本删除提交；已 fetch 并 rebase 到 `origin/main`，没有覆盖远端历史。
- rebase 后主提交已成功推送到 `origin/main`。
