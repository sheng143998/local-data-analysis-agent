# 当前 Handoff

## 品类订单商品数与销售额排行失败修复（已完成）

- 计划：`docs/plans/2026-07-19-category-ranking-contract-repair.md`；完成记录：`docs/modules/2026-07-19-category-ranking-contract-repair.md`。
- 已完成：新增 `category_item_sales_ranking` 合同，已支付订单内按商品品类统计订单商品数和订单商品明细销售额；特异合同替代泛化销售额/商品数合同。“商品品类 / 品类 / 类目 / 分类”统一为 `category`，不会再要求额外 `product` 输出。
- 验证：Resolver/Planner/Inspector/Graph focused `71 passed`；迁移 `015` 已应用；真实本地只读目标 SQL 通过 Inspector、Guard 和 EXPLAIN，执行成功返回 10 行；前端构建通过。
- 风险：云端 SQL 模型仍可能超时、返回空 `sql` 或非 JSON；此时系统仍会安全失败，需后续独立改善模型可用性，不得使用固定 SQL 绕过链路。
- 交付：`46cd7a6`（`修复品类商品排行合同`）已推送至 `origin/main`。

## 图表业务标签与量纲坐标轴修复（已完成）

- 计划：`docs/plans/2026-07-19-visualization-business-labels-and-axes.md`。
- 完成记录：`docs/modules/2026-07-19-visualization-business-labels-and-axes.md`。
- 已完成：图表使用确定性业务字段标签；销售额与订单数按货币/数量分轴，月度图标题为“订单数、销售额趋势”，时间轴不展示 ISO 时区文本。
- 验证：Result Contract 与 Presenter `11 passed`、前端构建通过；真实月度查询契约包含月份/订单数/销售额标签和 number/currency 单位。

## 聊天子视图与结果排序展示修复（已完成）

- 计划：`docs/plans/2026-07-19-chat-subpage-and-result-ordering.md`。
- 完成记录：`docs/modules/2026-07-19-chat-subpage-and-result-ordering.md`。
- 已完成：聊天工作区改为视口受控的独立滚动子视图，SQL/图表/表格默认折叠为查询详情；Presenter 保留 SQL 排序并压缩日期显示。
- 验证：Presenter `5 passed`、前端构建通过；真实月度查询摘要首行修正为 2017-01 / 800。自动化浏览器无法访问宿主机本地端口，UI 截图验证待本机浏览器确认；Vite 已启动于 `http://127.0.0.1:5173`。

## 可执行 Query Plan 与失败诊断修复（已完成）

- 计划：`docs/plans/2026-07-19-executable-query-plan-and-failure-diagnostics.md`。
- 完成记录：`docs/modules/2026-07-19-executable-query-plan-and-failure-diagnostics.md`。
- 已完成：Query Plan 增加可执行合同，按月已支付订单问题绑定时间列、支付谓词、订单粒度去重策略和技术别名；生成/Repair 直接消费合同。管理员运行详情可见候选 SQL 最小摘要；503 前端文案不再错误要求用户重新描述已充分的问题。
- 验证：focused `65 passed`、前端生产构建通过；真实认证运行 `3fb6119c-efe4-444b-8727-9d5f904f1dd7` Guard 放行、执行成功、返回 12 行。全量后端集成仍受云端模型非确定性影响，详见模块记录。

## 本地管理员账号创建（已完成）

- 计划：`docs/plans/2026-07-19-local-admin-account-reset.md`。
- 完成记录：`docs/modules/2026-07-19-local-admin-account-reset.md`。
- 已创建：本地开发管理员显示名为 `admin`，登录邮箱为 `admin@example.com`。接口要求标准邮箱，故不使用 `admin@localhost`。
- 验证：现有登录接口认证成功且返回 `admin` 角色；不在文档、日志或提交中记录密码或密码哈希。

## 通用对话模型本地配置（进行中）

- 计划：`docs/plans/2026-07-19-dialogue-model-local-config.md`。
- 范围：仅向 Git 忽略的 `backend/.env` 添加 `DIALOGUE_MODEL_*` 占位项，默认关闭，由用户填写 provider、endpoint、模型和 Key；不改应用代码或 SQL 链路。
- 已完成：`docs/modules/2026-07-19-dialogue-model-local-config.md`。本地配置占位项已添加，Settings 读取验证通过，`.env` 受 Git 忽略保护；不提交本地配置或密钥。提交推送待本模块 Git 操作完成。

## Top N、成本与比率合同修复（进行中）

- 计划：`docs/plans/2026-07-18-topn-cost-rate-contract-fix.md`。
- 目标：修复 `database_022` Top N 被误作 filter、`028` 成本合同缺失、`035` 比率格式和 `043` 复购严格口径问题；不要求用户手动补充指标。
- 验证：Planner/Inspector/Presenter focused tests 与真实 `013/022/028/035/043` 对照；不提交评测报告。

## 批量评测耗时与日志可观测性（进行中）

- 计划：`docs/plans/2026-07-18-batch-evaluation-observability.md`。
- 目标：解决 29 条长批评测超时后报告不落盘的问题，为每个 case 保留 API 总耗时、Graph 节点耗时、模型/Repair 摘要、最慢节点和失败分类，并支持 checkpoint 恢复。
- 范围：顺序执行不改为并发；不记录 prompt、密钥、原始模型输出或敏感结果行；不改 SQL 安全和业务口径。
- 验证：eval runner focused tests、替身 analyzer 小批 checkpoint/resume 验证、diff 检查；真实报告继续仅为本地工件。
- 已完成：`docs/modules/2026-07-18-batch-evaluation-observability.md`。批量报告新增 API/Graph/未归因耗时和节点 p50/p95 聚合，目标评测每 case 原子 checkpoint 并支持 `--resume`。验证：eval runner `18 passed, 1 warning`、eval scripts compileall 和 diff 检查通过。提交推送待本模块 Git 操作完成。

## 语义 Router 与合同 SQL 强制改造（进行中）

- 计划：`docs/plans/2026-07-18-semantic-router-and-contract-sql.md`。
- 目标：以安全规则优先、受限语义分类、确定性复核和保守降级替换单关键词 Router 误路由；将已确认 Semantic Contract/Query Plan 转成 SQL 生成后的阻断性业务口径校验。
- 范围：Router 不传 schema/SQL/rows；危险和待澄清状态仍由确定性规则优先；SQL 不满足合同只可有限 Repair 或失败，不得以固定业务 SQL 绕过模型与安全链路。
- 当前已知问题：`dialogue_router.py` 当前仅按数据关键词分流，会将“如何提升用户体验”等普通问题误入数据分析；`analysis_graph.py` 仍有 `_single_order_count_fallback`，与不写死 SQL 的主链路目标不一致。本轮会移除该主链路 fallback。
- 验证：Router focused tests、10 条固定意图样本、合同 SQL focused tests、上轮 50 case 中答案/严格失败样本及稳定随机 5 条；报告仅保留为本地工件，不提交。
- 联网调研：已获取 Snowflake Semantic Views 与 dbt Semantic Layer 官方资料；ChatGPT 内部实现未公开，因此只采用结构化输出、置信度、保守回退与语义层这些可验证模式。
- 已完成 Router 子模块：`docs/modules/2026-07-18-semantic-dialogue-router.md`。规则关键词路由已替换为安全规则优先、受限语义模型、确定性数据证据复核和保守回退；Router 不传 schema/SQL/rows。验证：focused `23 passed`，云端 `qwen3.7-plus` 的 10 条中文样本 `10/10`，模型分类 9 条、确定性结果解释 1 条。Router 8 秒超时不足，已调为 20 秒；此前 `Arrearage` 与后续读超时均已作为外部服务状态记录。交付：`71202bd` 已推送。
- 已完成合同 SQL 子模块：`docs/modules/2026-07-18-contract-sql-enforcement.md`。Query Plan 已携带合同字段/聚合约束，Inspector 在 Guard 前拒绝合同来源、聚合、过滤、输出、排序和 Top N 不一致 SQL；固定订单数 fallback 已移除。focused `61 passed`、compileall 和 diff 检查通过。首次目标评测为 `11/29` 执行、`3/29` 严格、`4/28` 答案，17 条受云端 503 影响；第二次目标评测 30 分钟超时且无报告，评测 checkpoint 是下一优先事项。提交推送待本模块 Git 操作完成。

## ChatGPT 体验与通用对话 Agent 升级（进行中）

- 总计划：`docs/plans/2026-07-13-chat-experience-and-dialogue-agent-upgrade.md`。
- 目标：消除前端业务 Mock、升级聊天页与长历史治理、接入真实流式输出和图表，并以安全 Dialogue Router 支持通用聊天、澄清、结果解释和 SQL 分析。
- 已完成首个模块：会话列表/消息窗口分页。子计划：`docs/plans/2026-07-13-conversation-pagination.md`；记录：`docs/modules/2026-07-13-conversation-pagination.md`。`GET /api/conversations` 已改为 cursor page，详情接口支持 `limit/before` 消息窗口和 `has_more/next_before`；InMemory、Redis/PostgreSQL 回退、前端类型/client 与 API 文档已同步。验证：会话 focused `13 passed, 1 warning`、前端构建通过、`git diff --check` 通过。`bc6f076` 已推送至 `origin/main`。
- 已完成模块：ChatGPT 风格聊天页与虚拟消息窗口。子计划：`docs/plans/2026-07-13-chat-page-virtualized-ui.md`；记录：`docs/modules/2026-07-13-chat-page-virtualized-ui.md`。聊天页已消费分页契约，加入动态高度虚拟列表、向上加载滚动锚点、会话分页/搜索、新会话状态和固定输入区；`SqlPanel` 已移除 Mock SQL 默认值。验证：前端构建、Vite HTTP 200、聊天路径无 Mock 引用、`git diff --check` 通过；`test:e2e` 被已启用鉴权的旧未登录 smoke 阻断，未作为通过结果。`0c0ad56` 已推送至 `origin/main`。
- 已完成模块：Result Contract 可视化规格与真实图表。子计划：`docs/plans/2026-07-13-result-contract-visualization.md`；记录：`docs/modules/2026-07-13-result-contract-visualization.md`。`AnalyzeResponse.visualization` 由 Result Contract、真实列和 rows 确定性生成 `line`、`bar`、`pie` 或 `none`；ChatPage 的 ECharts 只消费该规格和真实 rows，不接收模型图表配置，也不改变 SQL 链路。验证：builder/presenter focused `9 passed`、前端生产构建和 Vite HTTP 200、结果组件/聊天页无 Mock 引用、`git diff --check` 通过。`backend/tests/test_api.py` 在 124 秒本机窗口内未完成，不能视为通过。交付：`0b923a4` 已推送至 `origin/main`。
- 已完成模块：数据分析 SSE 真实流式输出。子计划：`docs/plans/2026-07-13-analysis-sse-streaming.md`；记录：`docs/modules/2026-07-13-analysis-sse-streaming.md`。新增认证保护的 `POST /api/analyze/stream`，以 `stage`、`result`、`error` 和 `done` 传输真实服务节点和完整结果；ChatPage 使用 `ReadableStream` 消费、支持 AbortController 取消并复用最终 SQL/图表/结果表。当前不生成或伪造 `text_delta`，SQL 安全链路不变。验证：SSE/会话 focused `15 passed, 1 warning`、前端构建通过、SSE content type/事件顺序/错误/鉴权测试通过、`git diff --check` 通过。交付：`3207197` 已推送至 `origin/main`。
- 已完成模块：安全 Dialogue Router 与通用聊天。计划：`docs/plans/2026-07-14-dialogue-router.md`；记录：`docs/modules/2026-07-14-dialogue-router.md`。通用聊天、结果解释和拒绝默认不进入 Graph/数据库；明确数据问题保留 SQL 链路，待澄清会话优先续接。dialogue 模型独立配置且仅得到受限历史文本，不传 SQL/schema/rows。验证：Router/SSE focused `6 passed, 1 warning`、前端构建、diff 检查通过。交付：`9071a1d` 已推送至 `origin/main`。
- 安全边界：只有 `data_analysis` 可进入 Semantic Contract、Query Plan、Inspector、Guard 和只读 Executor；通用聊天默认不读取数据库、不发送完整 schema/SQL 到云端。
- 验证：分页 focused pytest、后续前端 build/e2e、SSE contract/router eval 和 authenticated 50-case 对照。每个模块通过后独立提交推送。
- 已完成子模块：前端业务 Mock 清理。计划：`docs/plans/2026-07-14-frontend-mock-removal.md`；记录：`docs/modules/2026-07-14-frontend-mock-removal.md`。`frontend/src/data/mock.ts` 已删除；查询历史、SQL Memory 与实时运行评估页改为只读真实管理员 API，数据源页面保持受限空态，遗留问答组件仅消费调用方传入的真实数据。验证：`npm.cmd run frontend:build` 通过、`data/mock` 源码扫描无匹配、`git diff --check` 通过。交付：`ce8d8b9`，推送待完成；`eval/reports/latest_eval_report.json` 和 `eval/reports/semantic_contract_v2_batch_002.json` 是用户/评测工件，不提交也不改动。
- 已完成子模块：Dialogue Router 澄清回归修复。计划：`docs/plans/2026-07-14-dialogue-router-clarification-regression.md`；记录：`docs/modules/2026-07-14-dialogue-router-clarification-regression.md`。业务概览短语现进入 `data_analysis` 并复用既有澄清策略，避免误走通用聊天；普通闲聊仍不进入 Graph。验证：Router、SSE、会话分页和可视化 focused pytest `28 passed, 1 warning`，`git diff --check` 通过。交付：`1ed9ad4` 已推送；本地评测工件继续不提交。
- 已完成子模块：明确数据问题的错误澄清防护。计划：`docs/plans/2026-07-14-intent-false-clarification-guard.md`；记录：`docs/modules/2026-07-14-intent-false-clarification-guard.md`。明确的对象/聚合/排行请求在模型空候选或意图模型不可用时会保留为自然语言候选，不再错误澄清；模糊概览保留追问。验证：意图、路由、会话、SQL 选择和澄清 focused `68 passed, 1 warning`；独立认证报告 `chat_upgrade_full_eval_20260714_v4.json` 为执行 `25/50`、严格 `13/50`、答案 `14/48`，错误澄清为 0、剩余 25 条均为空 SQL。该结果仍低于执行基线 `31/50`，整体升级不能收口。云端意图模型连接现已恢复；最新全量报告见 `docs/modules/2026-07-14-cloud-intent-recovery-evaluation.md`，结果为执行 `30/50`、严格 `12/50`、答案 `14/48`，仍未达到基线。当前主瓶颈是本机 `qwen2.5-coder:3b` 的空 SQL/Guard 失败；下一步需稳定且获批准的 SQL 模型，不得用固定 SQL 绕过链路。交付：`4dc5466` 已推送；独立评测报告与原有本地评测工件均不提交。
- 已完成子模块：空 SQL 的受控修复重试。计划：`docs/plans/2026-07-14-empty-sql-repair-retry.md`；记录：`docs/modules/2026-07-14-empty-sql-repair-retry.md`。首次空 SQL 现在也进入一次 Repair Prompt，第二次空 SQL 严格失败，不形成循环且不使用固定 SQL。验证：Graph/Generator focused `52 passed`；认证前 10 条抽样仍为 `4/10`，本机 3B 模型在重试也未产生 `sql`，不得将此改动表述为质量提升。整体升级仍不能收口，需稳定且获批准的模型配置重跑全量对照；交付：`dc53686` 已推送。独立评测报告和原有本地工件不提交。

## README 与展示文档刷新（已完成，已提交并推送）

- 任务计划：`docs/plans/2026-07-13-readme-documentation-refresh.md`。
- 范围：同步 README、架构、Agent 工作流、评估说明和项目结构，修正旧 mock/固定模板/测试数字描述，补充已交付升级阶段与 authenticated 50-case 基线。
- 当前风险：`eval/reports/latest_eval_report.json` 和 `eval/reports/semantic_contract_v2_batch_002.json` 是本地未提交评测工件；文档只引用可信的 `post_upgrade_full_eval.json` 和 `ground_truth_text_alignment.json`。
- 已完成：README、架构、Agent 工作流、评估说明和项目结构均已同步当前实现，不再保留 mock 闭环、旧测试数字或过期评估结论。
- 验证：Markdown 相对链接 `MARKDOWN_LINKS_OK`、目标文档 UTF-8 读取通过、`git diff --check` 通过；模块记录：`docs/modules/2026-07-13-readme-documentation-refresh.md`。
- 交付：`c991e74`（`同步README与Agent展示文档`）已推送至 `origin/main`。

## 本轮升级交付状态

- 复合数据 Agent 升级 Phase 0-7 已完成代码与文档交付：可信 authenticated 基线、Semantic Contract/Resolver、Clarification Policy、Trusted SQL、Query Plan/Context Pack、Inspector/Repair、Result Contract/Presenter 和 Model Routing/Observability 均已落地并推送。
- 本轮新增提交：`fdcfcd1`（SQL Inspector/Repair + 交易状态语义契约并行集成）、`ef14aa0`、`5a65b26`、`d8ba195`、`7b7c9a0`（真值文本/元数据评测交付）、`f81ee39`（升级计划和 handoff 收口）。
- 可信质量基线仍为 `eval/reports/post_upgrade_full_eval.json`：执行 `31/50`、严格 `13/50`、答案 `14/48`；这证明链路可追踪但尚未达到质量门槛。下一轮优先用稳定模型配置重跑 50 case 并按失败分类优化，不得以固定 SQL 绕过安全链路。

## SQL Inspector/Repair 质量专项（已完成，已提交并推送）

- 任务计划：`docs/plans/2026-07-13-sql-repair-rule-contract.md`。
- 目标：将 Inspector 分类 issue 转为可复制的模型修复规则，改善 Query Plan 对齐和生成 SQL 修复；不写固定 SQL、不修改语义契约或评测报告。
- 当前证据：`eval/reports/post_upgrade_full_eval.json` 中严格成功 `13/50`；失败 trace 主要出现实体表/度量遗漏、排行排序/Top N、时间粒度与错误支付口径，现有 repair prompt 对 Inspector 类别仅传递通用文本。
- 已完成：Inspector 分类 issue 现在附带可复制 `repair_rule`；SQL generator payload 显式区分 Query Plan 必需约束和召回上下文候选，Repair Prompt 按类别透传规则；未增加固定 SQL或放宽安全边界。模块记录：`docs/modules/2026-07-13-sql-repair-rule-contract.md`。
- 验证：Inspector/Generator `19 passed`；Graph/Planner/Validator 回归 `49 passed`；主线收口 focused 合计 `55 passed`；`git diff --check` 通过。该专项未单独重跑 authenticated benchmark，评测基线未被修改。
- 交付：`fdcfcd1` 已推送至 `origin/main`；并行语义契约文件因共享 Git index 同批进入该提交，未改写历史。

## 当前状态

- 已完成（并行评测子任务）：Ground Truth Text Alignment And Authenticated Evaluation。计划：`docs/plans/2026-07-13-ground-truth-text-alignment.md`；记录：`docs/modules/2026-07-13-ground-truth-text-alignment.md`；对照报告：`eval/reports/ground_truth_text_alignment.json`。外部 `新建 文本文档.txt` 与 JSONL 真值集均为 50 条，问题/答案差异均为 0，4 条特殊结果模式一致。认证第 1 批 `ground_truth_current_batch_001.json` 已完成 `7/10` 执行、`3/10` 严格、`3/10` 答案匹配；`database_001` 返回 `99440` 对真值 `99441`，Guard 允许且 trace 为 `model_rewrite`，归类为语义/模型生成口径偏差，不是鉴权问题。未修改核心 graph、Prompt、Guard 或 Executor；提交 `ef14aa0`、`5a65b26`、`d8ba195`、`7b7c9a0` 已推送至 `origin/main`。

- 进行中：Handoff State Consolidation。计划：`docs/plans/2026-07-13-handoff-state-consolidation.md`。仅清理已完成模块遗留的重复状态，明确当前可信评测报告与未提交评测工件；不修改应用或评测内容。

- 当前已推送：`39e1b8e`（复杂语义契约/Query Plan）、`0b64e7c`（SQL EXPLAIN 预检）、`3caef13`（可信 SQL 指纹）、`219101c`（空结果语义展示）。各模块记录位于 `docs/modules/2026-07-13-*.md`。

- 可信 50-case 对照仍以 `eval/reports/post_upgrade_full_eval.json` 为准：执行 `31/50`、严格 `13/50`、答案 `14/48`。本机 `eval/reports/latest_eval_report.json` 是后续运行的标准 20 题工件（执行 `8/20`、严格 `6/20`），不替代该基线；`eval/reports/semantic_contract_v2_batch_002.json` 是未提交的认证第 11-20 题工件。

- 当前主要风险：本地 `qwen2.5-coder:3b` 会产生空 SQL 或错误分组 SQL；安全链路已收紧，质量改进必须通过稳定的 authenticated 50-case 复测证明。后端全量/API 组合测试在本机 120 秒窗口内多次未完成，不能视为全绿。

- 下一步：在现有语义契约、Query Plan、Inspector 和模型路由基础上，重新运行稳定的 authenticated 50-case 对照，比较模型配置并按失败分类提升质量；不通过固定 SQL 绕过模型、Inspector、Guard 或 Executor。

- 已完成（并行模块）：Transaction State Semantic Contract Coverage。计划：`docs/plans/2026-07-13-transaction-state-semantic-contract-coverage.md`；记录：`docs/modules/2026-07-13-transaction-state-semantic-contract-coverage.md`。新增订单状态分布、支付状态分布、支付方式记录数与支付方式已支付金额四个版本化契约，并让契约声明性过滤器进入 Query Plan；真实 PostgreSQL 已应用 `013`，Resolver/Planner/migration focused `18 passed`。未写固定 SQL、未放宽安全链路；改动随 `fdcfcd1` 推送。完整 authenticated 50-case 仍需后续以稳定模型配置复测。

- 已完成：Contract And Plan Prompt Enforcement Experiment（已撤回）。报告：`eval/reports/contract_plan_prompt_batch_001.json`；记录：`docs/modules/2026-07-13-contract-plan-prompt-enforcement.md`。Prompt 强约束导致 authenticated 前 10 条从 `7/10`、`3/10`、`3/10` 回归到 `6/10`、`2/10`、`2/10`，已从主链路撤回。结论：不以单次 Prompt 规则替代语义资产/Inspector。

- 进行中：Contract And Plan Prompt Enforcement。计划：`docs/plans/2026-07-13-contract-plan-prompt-enforcement.md`。完整 benchmark 显示无关 payments/context 约束与模型空 SQL 是主失败源；将按已绑定契约/Plan 收紧 Prompt 和 Inspector，不写固定 SQL、不放宽 Guard。

- 已完成：Upgrade Full Benchmark。报告：`eval/reports/post_upgrade_full_eval.json`；记录：`docs/modules/2026-07-13-upgrade-full-benchmark.md`。相同 authenticated 50-case 真值集对比：执行成功 `28/50 -> 31/50`，严格成功 `11/50 -> 13/50`，答案匹配 `10/48 -> 14/48`。升级有可复现提升但远未达到质量门槛；下一步以失败分类扩展审核语义资产/verified SQL，并 benchmark SQL 模型。

- 已完成：Entity Total Semantic Contracts。计划：`docs/plans/2026-07-13-entity-total-semantic-contracts.md`；记录：`docs/modules/2026-07-13-entity-total-semantic-contracts.md`；报告：`eval/reports/entity_contract_batch_001.json`。10 个基础实体契约已传入 SQL Prompt；前 10 条严格成功和答案匹配从 `2/10` 提升至 `3/10`，执行成功维持 `7/10`。无固定 SQL；复杂口径仍待进一步语义资产和模型评测。

- 进行中：Entity Total Semantic Contracts。计划：`docs/plans/2026-07-13-entity-total-semantic-contracts.md`。benchmark 已证实基础表真值正确，失败来自模型将多个实体总数误生成为订单数；将补齐契约并把定义透传 SQL Prompt，不增加固定 SQL。

- 已完成：Upgrade Benchmark Batch 001。报告：`eval/reports/post_upgrade_batch_001.json`；记录：`docs/modules/2026-07-13-upgrade-benchmark-batch-001.md`。升级后前 10 条执行成功 `7/10`，较升级前 `5/10` 提升；严格成功和答案匹配均仍为 `2/10`。结论：链路稳定性改善，业务口径/SQL 准确性仍是主瓶颈，不能将当前升级视为完成。

- 已增强：Model Routing And Observability。SQL generator/repair 已使用显式路由，run trace 记录 provider/model/latency 摘要而不记录 prompt 或密钥。验证：SQL generator/run trace/routing `17 passed, 1 warning`。模型选择仍必须通过 authenticated benchmark。

- 已增强：Trusted SQL Repository 管理。管理员可通过 `PATCH /api/memories/{memory_id}/trust` 显式审核并提升 SQL Memory 状态，只有 `verified` 可 fast path；仍经过 QuerySpec、Inspector、Guard 和 Executor。验证：Memory/API/reuse `21 passed, 1 warning`。schema/契约 fingerprint 待后续自动化。

- 已完成：Model Routing Foundation（Phase 7 起始）。计划：`docs/plans/2026-07-13-model-routing-observability.md`；记录：`docs/modules/2026-07-13-model-routing-foundation.md`。任务角色到 provider/model/base URL 的集中路由已建立，意图解析已接入；不记录密钥或完整 prompt。验证：focused `22 passed`。待完成：SQL adapter/run trace 路由摘要和 benchmark 驱动模型比较。

- 进行中：Model Routing And Observability（Phase 7）。计划：`docs/plans/2026-07-13-model-routing-observability.md`。将意图、SQL、展示任务与现有 provider/model 配置显式关联，并记录安全摘要；不更改 endpoint、不向未批准云端发送 SQL/schema。

- 已完成：Result Contract And Presenter（Phase 6）。计划：`docs/plans/2026-07-13-result-contract-presenter.md`；记录：`docs/modules/2026-07-13-result-contract-presenter.md`。内部 Contract 已把 Query Plan、真实列角色、行、范围和告警交给 Presenter；展示优先使用已确认度量标签，对外 API 不变。验证：focused `36 passed`、API/Presenter `4 passed`、后端全量 `241 passed, 1 warning`。风险：前端尚未消费列角色，图表/结构化来源展示待 UI 专项。

- 进行中：Result Contract And Presenter（Phase 6）。计划：`docs/plans/2026-07-13-result-contract-presenter.md`。将 Query Plan、执行列/行、范围和告警变为内部 Result Contract，Presenter 以真实形态生成摘要，不改公开 API。

- 已完成：SQL Inspector And Categorized Repair（Phase 5）。计划：`docs/plans/2026-07-13-sql-inspector-repair.md`；记录：`docs/modules/2026-07-13-sql-inspector-repair.md`。Inspector 已在 Guard 前依据 Query Plan 检查实体、排行排序、Top N、时间过滤并输出分类 issue 给有限 repair；Guard/Executor 未放宽。验证：focused `35 passed`、后端全量 `240 passed, 1 warning`。风险：EXPLAIN/探针查询与复杂 CTE 语义检查待后续增强。

- 进行中：SQL Inspector And Categorized Repair（Phase 5）。计划：`docs/plans/2026-07-13-sql-inspector-repair.md`。新增 AST+Query Plan 对齐检查并将分类失败交给现有有限 repair；Guard/Executor 保持最终安全边界。

- 已完成：Query Plan And Context Pack（Phase 4）。计划：`docs/plans/2026-07-13-query-plan-context-pack.md`；记录：`docs/modules/2026-07-13-query-plan-context-pack.md`。结构化 Plan 已贯通 intent、Graph、Context Builder 和 SQL payload，限制实体、度量、维度、时间、排序、limit 与预期结果形态；未知概念不猜测 SQL。验证：focused `46 passed`、后端全量 `238 passed, 1 warning`。下一步：Inspector 将以 Plan 对齐作为执行前检查。

- 进行中：Query Plan And Context Pack（Phase 4）。计划：`docs/plans/2026-07-13-query-plan-context-pack.md`。从 QuerySpec、已解析契约和 intent 产生受限计划，并裁剪传给 SQL 模型的上下文；不改变 SQL 安全边界或让 Plan 直接执行 SQL。

- 已完成：Trusted SQL Repository Foundation（Phase 3）。计划：`docs/plans/2026-07-13-trusted-sql-repository.md`；记录：`docs/modules/2026-07-13-trusted-sql-repository.md`。SQL Memory 生命周期已持久化：新成功 SQL 为 `executed`，旧记录默认为 `reviewed`，只有 `verified` 允许 fast path。验证：SQL Memory/Graph focused `42 passed`。风险：管理员审核提升、契约版本/schema hash 绑定与全量评测对照仍待后续子模块。

- 进行中：Trusted SQL Repository（Phase 3）。计划：`docs/plans/2026-07-13-trusted-sql-repository.md`。将 SQL Memory 分为 candidate/executed/reviewed/verified/deprecated/rejected，只有 verified 可 fast path；新成功 SQL 只记 executed，旧记录降级 reviewed，并绑定契约/schema 版本元数据。所有 SQL 仍须经过 QuerySpec、Guard 和只读 Executor。

- 已完成：Clarification Policy（Phase 2）。计划：`docs/plans/2026-07-13-clarification-policy.md`；记录：`docs/modules/2026-07-13-clarification-policy.md`。独立 Policy 已以结构化缺失业务对象/契约冲突决定追问，Resolver 不再直接生成澄清文案；未知明确概念与低置信度均不会单独触发追问。验证：focused `15 passed, 1 warning`、后端全量 `237 passed, 1 warning`。风险：自然追问生成和多次无进展熔断留待会话状态增强；真实评测将在下一 SQL/Planner 模块统一对照。

- 进行中：Clarification Policy（Phase 2）。计划：`docs/plans/2026-07-13-clarification-policy.md`。Resolver 将只报告契约匹配/冲突，独立 Policy 依据缺失槽位、冲突和动作输出结构化追问决定；未知明确概念和模型低置信度不得单独触发澄清。保持旧 pending 会话兼容，安全 SQL 边界不变。

- 已完成：Semantic Resolver Integration（Phase 1）。计划：`docs/plans/2026-07-13-semantic-resolver-integration.md`；记录：`docs/modules/2026-07-13-semantic-resolver-integration.md`。启用契约已以 key/展示名/同义词绑定 intent，并透传至 Graph 检索上下文和 SQL Prompt；未知明确概念继续开放式处理，契约不执行 SQL。migration `009` 已初始化 3 个基础快照契约。验证：focused `57 passed, 1 warning`、后端全量 `234 passed, 1 warning`。Phase 2 将独立 Clarification Policy 接管当前冲突澄清。

- 已完成（并行子任务）：Clarification Policy 实施设计（Phase 2）。计划：`docs/plans/2026-07-13-clarification-policy-implementation-design.md`。设计将对话解释器、Semantic Resolver、确定性 Policy 与自然追问生成分离；定义结构化 `missing` / `conflict` / `action`、兼容旧 JSONB pending state 的方案、AgentService/续问的最小接入及完整测试/评测矩阵。当前 Resolver 在冲突时仍直接写 `needs_clarification` 和用户文案，Phase 2 主线须将该职责收回 Policy。验证：已核对现有函数、schema、repository、测试和 UTF-8 文档路径，`git diff --check` 通过。风险：既有持久化状态只支持 `metrics` / `time_range`，实施时必须兼容；Policy 不能把模型置信度或未命中词表当作自动澄清理由。本设计不单独提交，由主线集成提交。

- 进行中：Semantic Resolver Integration（Phase 1）。计划：`docs/plans/2026-07-13-semantic-resolver-integration.md`。将版本化启用契约接入意图、会话续问和 Graph 上下文：唯一匹配绑定结构化语义，冲突才触发确定性澄清，未知明确概念保持开放式检索/模型路径。不会让 Resolver 产生 SQL 或绕过 QuerySpec、Guard、只读 Executor。验证：Resolver/意图/会话/Graph 聚焦测试、后端全量、前端构建和 authenticated 首批标准评测对照。

- 已完成：Evaluator Admin Configuration And First Database Batch。已创建本机专用管理员评测账号，随机凭据仅写入未跟踪 `backend/.env`，没有修改既有管理员密码，也没有提交凭据。`npm.cmd run eval:database-baseline -- --start 0 --limit 10 --report eval/reports/database_batch_001.json` 已完成：执行成功 `5/10`、严格成功 `2/10`、答案匹配 `2/10`、平均 `26,234ms/case`。完整 50 case 需要继续运行 `start=10/20/30/40` 五个独立批次并核对 coverage；当前低成功率是语义/SQL 生成质量基线，不能当作鉴权失败。

- 已完成：Full Database Ground Truth Baseline。完整 50 case 已通过 authenticated runner 执行并写入 `eval/reports/latest_eval_report.json`：执行成功 `28/50`（`56.00%`）、严格成功 `11/50`（`22.00%`）、答案匹配 `10/48`（`20.83%`）、平均 `26,707ms/case`。该基线确认评测账号与管理员 trace 可用，也明确当前首要质量缺口是 SQL 生成/语义口径，而非鉴权；后续每个 Phase 1+ 模块需与此报告对比。

- 已完成：Semantic Contract Data Foundation（Phase 1）。计划：`docs/plans/2026-07-13-semantic-contract-data-foundation.md`；完成记录：`docs/modules/2026-07-13-semantic-contract-data-foundation.md`。`semantic_contracts` 已通过 `contract_key + version` 保留指标、维度、实体和关系的历史口径；repository 默认读取最高启用版本且只允许新增版本，不修改现有 Graph、QuerySpec、Guard 或只读 Executor。真实 PostgreSQL 已应用 migration `008`。验证：focused `9 passed`、后端全量 `228 passed, 1 warning`。后续将按 Resolver 集成设计接入运行链路，未知但明确概念仍保留开放式 schema/模型路径。

- 已完成（并行子任务）：可恢复分批评测。计划：`docs/plans/2026-07-13-evaluation-resumable-batches.md`；记录：`docs/modules/2026-07-13-evaluation-resumable-batches.md`。runner 支持 `--start`、`--limit` 和独立 `--report`，报告包含数据集总量、选择范围、已运行 case ID 与完整性标记；非法参数会在模型执行前阻断，鉴权及质量定义未变。验证：`.venv` 聚焦测试 `17 passed, 1 warning`，CLI 帮助通过。风险：每个分批报告仅代表该批，主线汇总完整 50 题前必须核对 case ID 覆盖；本子模块不单独提交/推送，由主线集成。

- 进行中（并行子任务）：Semantic Resolver 集成设计（Phase 1）。计划：`docs/plans/2026-07-13-semantic-resolver-integration-design.md`。范围：梳理意图、会话续问、QuerySpec、检索和 Graph 的最小接入边界，形成数据流、测试矩阵和风险；不修改共享运行代码、migration 或 SQL 安全链路。验证：UTF-8 文档路径、函数名和数据流与当前代码核对。风险：必须依赖并行 Semantic Contract 数据基础层的公开 schema/repository，不能创建重复模型。

- 已完成（并行子任务）：管理员评测账号安全核验。计划：`docs/plans/2026-07-13-evaluator-admin-account-validation.md`；记录：`docs/modules/2026-07-13-evaluator-admin-account-validation.md`。已确认启用管理员账号与评测登录/run trace 权限路径，且缺失 `EVAL_AUTH_*` 会在评测前明确阻断。主线必须将已知管理员凭据写入未跟踪 `backend/.env` 后运行 `npm.cmd run eval:database-baseline`；不允许用 analyst 账号替代，否则会丢失管理员 trace。该并行核验按主线边界不单独提交。

- 已完成（并行子任务）：Semantic Contract 数据基础层（Phase 1）。计划：`docs/plans/2026-07-13-semantic-contract-data-foundation.md`；记录：`docs/modules/2026-07-13-semantic-contract-data-foundation.md`。新增 `semantic_contracts` 的版本化 migration、Pydantic schema 和 repository；按 `contract_key + version` 保留历史口径，默认读取最新启用版本，且只新增版本不覆盖既有定义。未改 `analysis_graph`、意图 Resolver 或 SQL 安全链路。验证：项目 `.venv` 聚焦测试 `9 passed`；系统 Python 因缺少 `langgraph` 无法加载 conftest；`npm.cmd run backend:test` 在 124 秒超时且未产生失败输出，未计为通过，主线集成后必须重跑。风险：migration 尚待真实 PostgreSQL 应用验证；与 `metric_definitions` 暂时并存。本子模块按并行协作约定不单独提交或推送。

- 进行中：Compound Data Agent Upgrade Execution。总计划：`docs/plans/2026-07-13-compound-data-agent-upgrade-execution.md`；用户已批准按升级草案执行，并要求采用多 agent 并行开发。当前先验证并配置本机未跟踪的专用管理员评测凭据，运行 50 case 真值基线；并行准备 Semantic Layer V2 的迁移/repository 设计和现有意图/上下文接入点。每个阶段保持独立计划、验证、模块记录、commit 和 push。风险：不得暴露凭据或把配置失败记为模型质量，migration 与核心 graph 改动由主线统一集成。

- 已完成：Authenticated Ground Truth Evaluation（升级草案 Phase 0）。计划：`docs/plans/2026-07-13-authenticated-ground-truth-evaluation.md`；完成记录：`docs/modules/2026-07-13-authenticated-ground-truth-evaluation.md`。评测在 `AUTH_REQUIRED=true` 时会使用显式 `EVAL_AUTH_EMAIL` / `EVAL_AUTH_PASSWORD` 登录，并在整个批次复用一个会话；缺少凭据或登录失败会在执行 case 前明确阻断，不再产生误导性的 401 质量报告。用户提供的 50 条真实数据库问答已固化为 `eval/datasets/database_ground_truth_questions.jsonl`，报告新增结构化行结果的答案匹配状态、原因与匹配率；新增 `npm.cmd run eval:database-baseline`。验证：focused `14 passed, 1 warning`、后端全量 `223 passed, 1 warning`、前端构建通过。真实数据库基线尚未执行，原因是本机未配置专用评测凭据，命令已按设计明确阻断且未生成伪造报告。风险：需配置管理员评测账号才可采集 run trace；复杂多行/不可计算语义会在后续 Result Contract 阶段升级为结构化断言。模块提交 `f0dd341` 已推送至 `origin/main`。

- 待审查：复合式数据分析 Agent 升级改造草案。计划：`docs/plans/2026-07-13-compound-data-agent-upgrade-draft.md`；文档交付记录：`docs/modules/2026-07-13-compound-data-agent-upgrade-draft.md`。草案综合 Semantic View/MDL、Trusted SQL、Knowledge Store、Query Checker/Inspect、Tool Memory 等成熟机制，规划 Semantic Layer V2、确定性 Clarification Policy、Verified Query 分级、Query Plan、独立 Inspector、`EXPLAIN`/探针验证、Result Contract、authenticated evaluation 和模型路由。推荐下一步只实施 Phase 0：恢复鉴权评测与可信基线；当前未修改业务代码、数据库、API、配置或前端。

- 已完成：Current Aggregate SQL Repair。计划：`docs/plans/2026-07-12-current-aggregate-sql-repair.md`；完成记录：`docs/modules/2026-07-12-current-aggregate-sql-repair.md`。已补充当前快照、实体总量和支付口径的通用意图/SQL Prompt 约束，并为 `orders.status = 'paid'` Guard 错误加入明确 Repair 规则；没有增加固定用户数 SQL。截图 503 对应的无效支付谓词被 Guard 安全阻断；更新后真实只读重试生成 `COUNT(DISTINCT users.id)` 并返回 `99441`。验证：focused `57 passed`、后端全量 `219 passed, 1 warning`、前端构建通过。风险：本地 3B SQL 模型仍有输出波动，展示层仍将用户总量误称为销售趋势；标准评测缺鉴权测试会话。模块提交将在本次交付后记录。

- 已完成：Cloud Dialogue Model Connectivity。计划：`docs/plans/2026-07-12-cloud-dialogue-model-connectivity.md`；完成记录：`docs/modules/2026-07-12-cloud-dialogue-model-connectivity.md`。已修复阿里云云端意图模型继承本机 SOCKS 代理而缺少 `socksio` 的问题，改为 provider 直连；本机意图调用预算为单次 45 秒。真实云端调用“当前用户总数”已返回 `source=llm`、`needs_clarification=false` 与用户总数语义候选；“我想修改”也返回模型生成的上下文追问。模型不可用时只会返回中性缺失信息提示，不再推荐固定经营指标。验证：focused `29 passed, 1 warning`、后端全量 `217 passed, 1 warning`、前端构建通过。风险：云端响应可能需要数十秒；鉴权环境中的标准评测仍缺测试会话。模块提交将在本次交付后记录。

- 已完成：Model First Clarification Flow。计划：`docs/plans/2026-07-12-model-first-clarification-flow.md`；完成记录：`docs/modules/2026-07-12-model-first-clarification-flow.md`。模型语义候选不会再被低置信度或弱词表匹配覆盖，完整问题可直接进入 SQL 链路；澄清只由模型显式判定缺少关键业务信息时触发。用户拒绝上一轮建议时会重读原问题，不再重复旧话术；前端回复摘要只展示一次。`INTENT_MODEL_*` 可安全接入云端对话语义模型，`MODEL_*` 保持 SQL 模型并继续经过 QuerySpec/Guard/只读 Executor。验证：focused `52 passed, 1 warning`、后端全量 `214 passed, 1 warning`、前端构建通过。标准评测在本机 `AUTH_REQUIRED=true` 下全部 `401`，已恢复旧报告，不作为质量结论。风险：云端意图模型不可用时仍会保守澄清；评测脚本需补认证测试会话。模块提交将在本次交付后记录。

- 已完成：Local API Target Alignment。计划：`docs/plans/2026-07-12-local-api-target-alignment.md`；完成记录：`docs/modules/2026-07-12-local-api-target-alignment.md`。前端被忽略的本地环境 API 目标已由 `127.0.0.1:8002` 同步为用户实际启动的 `127.0.0.1:8000`，并已重启 Vite。验证：前端 HTTP 200、后端健康检查通过、`/api/auth/login` 从 `127.0.0.1:3000` 的 credentialed CORS 预检为 HTTP 200、前端构建通过且 bundle 使用 `8000`。风险：本机后端端口变更后，必须同步 `.env.local` 并重启 Vite；错误账号密码仍属于正常鉴权错误。模块提交将在本次文档交付后记录。

- 已完成：Model Semantic Candidates。计划：`docs/plans/2026-07-12-model-semantic-candidates.md`；完成记录：`docs/modules/2026-07-12-model-semantic-candidates.md`。语义模型高置信的未知候选不再被 `metrics` 规范化阻断；`semantic_metrics`/`semantic_dimensions` 会透传到 SQL Prompt，用户总数等问题可进入检索和模型生成。标准 `metrics` 仅服务已定义口径、QuerySpec 和模型不可用时的确定性降级。验证：focused `20 passed`、后端全量 `211 passed, 1 warning`、标准评测 280 秒完成为 `13/20` 执行成功、`60.00%` 严格成功率。风险：未知指标缺少确认口径，质量仍依赖模型、schema 召回和 Guard。模块提交 `5a16460` 已推送至 `origin/main`。

- 已完成：Model First Order Count Fallback。计划：`docs/plans/2026-07-12-model-first-order-count-fallback.md`；完成记录：`docs/modules/2026-07-12-model-first-order-count-fallback.md`。订单数已从直接 fallback 改为模型生成、QuerySpec 校验、一次 Repair 优先；只有模型首次无 SQL 或 Repair 后仍不合规，才使用受控已支付订单数 SQL，并继续经过 Guard/只读 Executor。验证：focused `33 passed`，后端全量 `210 passed, 1 warning`；标准评测报告为 `12/20` 执行成功、`60.00%` 严格成功率，但进程 364 秒超时，未计为通过。模块提交 `66cb945` 已推送至 `origin/main`。

- 已完成：Order Count And Conversation Recovery。计划：`docs/plans/2026-07-12-order-count-and-conversation-recovery.md`；完成记录：`docs/modules/2026-07-12-order-count-and-conversation-recovery.md`。单一无维度订单数已使用 QuerySpec 受控 fallback，真实数据库 smoke 为 `99440` 且通过 Guard/只读 Executor；模型 `503` 前会保存安全失败摘要。会话已同步写入三天 TTL 的 PostgreSQL 副本，Redis 不可用或重启时仍能恢复。管理员可在聊天侧栏显式“迁移本机历史”，将匿名开发会话归属到当前账号；普通登录不自动迁移。本机 `AUTH_REQUIRED=true`，新验证服务为前端 `http://127.0.0.1:3002`、后端 `http://127.0.0.1:8002`。验证：focused `55 passed, 1 warning`，后端全量 `209 passed, 1 warning`，前端构建通过，migration 已应用；标准评测报告为 `13/20` 执行成功、`60.00%` 严格成功率，但进程在 364 秒超时，未计为通过。风险：Redis 仍未运行，复杂 SQL 仍依赖本地模型。模块提交 `377b48e` 已推送至 `origin/main`。

- 已完成：Semantic Intent Normalization。计划：`docs/plans/2026-07-12-semantic-intent-normalization.md`；完成记录：`docs/modules/2026-07-12-semantic-intent-normalization.md`。意图识别已调整为模型候选抽取、业务概念规范化、QuerySpec/检索上下文校验三层；预置别名只作为受控业务 ID 的规范化与模型不可用时的兜底，不再作为唯一理解入口。模型返回项目未定义指标时会澄清，不会直接进入 SQL 生成。已补充订单总数表达、自然语言模型候选与未知概念测试，以及云端 OpenAI-compatible 微调模型接入说明。验证：focused `9 passed`，后端全量 `205 passed, 1 warning`，标准评测 268 秒完成为 `13/20` 执行成功、`60.00%` 严格成功；模型输出有波动，单次结果不能视为稳定提升。风险：本地 3B 模型仍不稳定于复杂 SQL；新业务概念必须同步扩展指标定义与 QuerySpec，不可仅增加别名。模块提交 `2dc7154` 已推送至 `origin/main`。

- 已完成：Skill Git Delivery And Chinese Comments。计划：`docs/plans/2026-07-12-skill-git-delivery-and-chinese-comments.md`；完成记录：`docs/modules/2026-07-12-skill-git-delivery-and-chinese-comments.md`。Skill 已要求新增/修改注释默认使用中文并说明业务目的、规则、安全边界或取舍；每个通过验证的完整模块必须检查 git 状态、独立提交并推送，且不得混入无关用户变更。模块提交和 `origin/main` 推送随本轮交付完成，最终 hash 以 git log 为准。

- 已完成：Agent Conversation Memory Architecture 的 Phase 1、L1、L2、L3 基础实现。计划：`docs/plans/2026-07-12-agent-conversation-memory-architecture-draft.md`；完成记录：`docs/modules/2026-07-12-conversation-memory-l1-l2-l3.md`。`/api/analyze` 现支持会话 ID、PendingClarification、确定性 Follow-up Resolver、会话恢复和跨主体隔离；“看看最近情况”后补“销售额，2017年”会合并 QuerySpec 后再进入原有 SQL Guard/Executor。L1 默认 8K token 预算、1K 输出预留、60%/80% 摘要水位；L2 Redis adapter 写穿 72 小时会话，`local-data-agent-redis` 已返回 `PONG` 且真实 Redis save/get 通过；L3 仅保存明确偏好并支持版本替换和删除。验证：migration 成功、focused `9 passed, 1 warning`、后端全量 `202 passed, 1 warning`、前端构建通过；标准评测进程 304 秒超时（exit `124`），但已刷新 20 case 报告为 `12/20` 执行成功、`11/20` 严格成功。未实现：并发、多线程、乐观锁、幂等重试、Redis 原子操作、后台归并、OAuth、MFA、组织/租户和邮件流程；生产 Redis 部署、持久化和健康检查仍需后续专项。

- 已完成：Time Range Contract And Repair Rules。计划：`docs/plans/2026-07-12-time-range-contract-and-repair-rules.md`；完成记录：`docs/modules/2026-07-12-time-range-contract-and-repair-rules.md`。QuerySpec 已把明确日期、月、年、当天和本月转换为 `[start, end)` 时间契约，并贯通意图、Prompt 与 SQL 意图校验；Repair Prompt 已包含字段别名和完整时间谓词的可执行规则。验证：focused `51 passed`、后端全量 `188 passed`；标准评测在 244 秒超时，旧报告未被覆盖。下一步：缩短并稳定标准评测，再验证真实模型对 2017 年销售额问题的一次修复成功率。

- 已完成：Frontend Dev Server Port。计划：`docs/plans/2026-07-12-frontend-dev-server-port.md`；完成记录：`docs/modules/2026-07-12-frontend-dev-server-port.md`。Windows 排除 `5139-5238` 导致 Vite 绑定 `0.0.0.0:5173` 返回 `EACCES`；前端开发服务已改为 `127.0.0.1:3000` 并同步默认 CORS。验证：Vite 已监听 `127.0.0.1:3000`，HTTP 首页请求和前端构建均通过。

- 已完成：SQL Runtime Safety And Model Baseline。计划：`docs/plans/2026-07-12-sql-runtime-safety-and-model-baseline.md`；完成记录：`docs/modules/2026-07-12-sql-runtime-safety-and-model-baseline.md`。SQL Guard 已强制 LIMIT 并阻断危险函数，Executor 已使用只读事务和超时，模型无可执行 SQL 时返回 `503`，本地模型不再继承系统代理。验证：后端全量 `180 passed`、focused `64 passed`、前端构建通过；当前标准评测基线为 `9/20` 执行成功、`8/20` 严格成功。下一步：QuerySpec 驱动的意图/生成/修复/评测优化，以及独立只读运行账号和测试数据库。

- 已完成：QuerySpec Semantic Contract。计划：`docs/plans/2026-07-12-query-spec-semantic-contract.md`；完成记录：`docs/modules/2026-07-12-query-spec-semantic-contract.md`。用户、漏斗、优惠券和流量来源问题已进入统一 QuerySpec，并贯通意图、模型 prompt、SQL 校验和 SQL Memory；Memory 现在只记录最终 SQL 实际用表和语义维度。验证：后端 `184 passed`、前端构建通过；标准评测提升至 `11/20` 执行成功、`10/20` 严格成功。下一步：复杂指标公式/repair prompt 强化和 AST 语义评测，另行处理只读运行账号与测试数据库。

- 已新增项目内开发规范 Skill：`.agents/skills/local-data-analysis-development/`。后续代码、接口、数据库、前端、评测、配置、文档和重构任务均应先读取本 Skill 和 `docs/handoff/current.md`，在编码前创建计划并更新 handoff，完成后补模块记录和 handoff。
- Skill 规范草案：`docs/plans/2026-07-12-project-development-skill-draft.md`；完成记录：`docs/modules/2026-07-12-project-development-skill.md`。官方 Skill 校验器受本机 Python 缺少 `PyYAML` 阻塞，文件结构和 UTF-8 内容已人工复核。

- 项目已连接 GitHub：`https://github.com/sheng143998/local-data-analysis-agent`
- 当前分支：`main`
- 前后端目录已拆分：
  - `frontend/`: React + Vite + TypeScript 前端
  - `backend/`: FastAPI 后端
  - `docs/`: 草案、计划、handoff
- 当前普通用户产品方向：聊天式数据问答 + 指标口径 CRUD，不默认展示模型、数据库连接状态、SQL 记忆细节和评估报告。
- `/api/analyze` 已接入 PostgreSQL 指标口径和表结构上下文召回，当前仍使用固定销售趋势 SQL 模板。
- `/api/analyze` 已写入 `query_runs` 和 `tool_calls`，开发者可通过 `/api/runs` 查看运行记录。
- `/api/analyze` 已接入 SQL Memory 检索和成功写入，高置信历史成功问题可走 `fast_path` 复用 SQL。
- `/api/analyze` 已支持销售趋势 SQL 参数化模板，可解析“最近 N 天”并写入 `sql_memories.parameters`。
- `/api/analyze` 已接入 SQL Rewriter / Generator 最小切片，可识别“最近 90 天每月订单数是多少？”并生成月度订单数 SQL。
- `/api/analyze` 已接入 Top N 商品/品类销售额查询切片，可识别“销售额最高的前 10 个商品是什么？”和“哪个商品品类销售额最高？”。
- `/api/analyze` 已接入退款率 / 支付成功率查询切片，可识别“哪个商品品类退款率最高？”和“每个支付方式的成功率是多少？”。
- `/api/analyze` 已接入毛利率查询切片，可识别“最近 30 天毛利率最高的商品品类是什么？”。
- `/api/analyze` 已接入复购率 / 城市客单价查询切片，可识别“最近 90 天复购率是多少？”和“每个城市的客单价是多少？”。
- 已新增 Schema Metadata 自动同步能力，换库、导入新表或字段变化后可运行 `py -3 backend/scripts/sync_schema_metadata.py` 刷新 `schema_metadata`，避免继续堆固定 SQL 模板。
- 已新增统一 ModelAdapter 基础层，后续 SQL Generator / Rewriter 调用外部或本地 OpenAI-compatible 模型必须走 `backend/app/core/model_adapter.py`。
- 已新增 Model-backed SQL Generator 基础工具，可基于已召回 schema/metric 构造 prompt、调用 ModelAdapter、解析模型 JSON SQL；尚未接入 `/api/analyze` 主链路执行。
- `/api/analyze` 已通过 `MODEL_SQL_GENERATOR_ENABLED` 配置开关接入 Model SQL Generator 的 `cold_path` 尝试路径；默认关闭，开启后模型 SQL 仍必经 Guard / Executor，失败会回退确定性生成。
- 已新增标准问题评估集基础设施，`npm run eval:standard` 可运行 20 个 V1 标准问题并生成 `eval/reports/latest_eval_report.json`。
- 标准问题评估已增强断言指标，报告区分 `execution_success_rate` 和 `strict_success_rate`，并输出表/关键词断言失败案例。
- SQL Memory `fast_path` 已增加关键表约束，用户、流量、优惠券等问题缺少关键表时不再直接复用历史 SQL。
- 前端已新增统一 API Client，数据问答和指标 CRUD 都通过 `frontend/src/api/client.ts` 调用后端，并统一解析 FastAPI `detail` 为中文业务错误。
- `/api/analyze.rows` 已改为通用表格结构，前端聊天页会根据 SQL 真实结果列动态生成表头，减少对固定销售趋势字段的依赖。
- 前端 `AnalysisResponse` 已补齐后端 `trace` 和 `steps` 类型契约，但普通用户页面不展示内部追踪细节。
- 已新增统一检索评分基础层，metric、schema、SQL Memory 检索复用文本相似、关键词命中、集合重合和加权评分工具，为后续 embedding / pgvector 混合检索打基础。
- 已新增 EmbeddingAdapter 基础层，支持 OpenAI-compatible embeddings 和 deterministic 本地 fallback，后续 schema、metric、SQL Memory 向量化必须走统一入口。
- 已新增 Schema / Metric Embedding 同步能力，可把 `schema_metadata.embedding` 和 `metric_definitions.embedding` 写入 pgvector 字段；本模块不改普通用户 UI、不展示向量状态、不新增固定 SQL 模板。
- 已新增 pgvector 混合检索基础层，metric/schema retriever 会结合语义候选、文本相似、关键词和结构化分数排序；向量不可用时自动退回文本检索。
- 已新增 SQL Memory Embedding 混合检索，成功 memory 写入会同步 `question_embedding` / `sql_embedding`，检索时优先用 `question_embedding` pgvector 分数填充 `semantic_similarity`，不可用时回退文本相似。
- 已新增 SQL Memory 历史向量补齐能力，`py -3 backend/scripts/sync_embeddings.py --target memory` 可为旧 memory 回填 question/sql embedding。
- 已新增通用分析结果 Presenter，能根据 SQL 返回列动态识别维度列、数值列和比例列，生成中文摘要和指标卡，减少对固定销售趋势字段的依赖。
- 已新增数据上下文刷新命令，把 schema metadata 同步和 embedding 同步串成一个入口，服务于换库、换表后的检索资产刷新。
- 已为 embedding 同步增加 `--limit` / `--embedding-limit` 控制，方便真实 provider 下先小批量刷新和验证。
- 已为 embedding 同步增加 `--batch-size` / `--embedding-batch-size` 控制，减少真实 provider 下的逐条请求开销。
- 已为 embedding batch 失败增加单条重试，避免单条坏数据拖垮整批同步。
- 已为 embedding 同步增加 `--sleep-ms` / `--embedding-sleep-ms` 固定间隔限速，降低真实 provider 限流风险。
- 已为标准评估报告增加断言失败聚合诊断，帮助定位缺失表、失败类别和路径。
- 已新增 Schema 表关系上下文，从已召回字段推断 join hints 并提供给模型 SQL Generator，不新增固定 SQL 模板。
- 已为 SQL Validator 接入 `schema_metadata` 字段存在性校验，提前拦截模型编造字段。
- 已为 Schema Metadata 同步增加字段名启发式中文业务含义，提升换库后 schema 检索和 embedding 文档质量。
- 已为 Schema Metadata 同步增加历史泛化说明刷新开关，显式升级旧自动说明并保留人工说明。
- 已增强 `/api/runs` 工具调用摘要，记录上下文召回、SQL 生成和 Guard 诊断信息。
- 已为 `RetrievalContext.table_relationships` 接入 PostgreSQL 真实外键读取，换库后优先使用数据库约束生成 join hints，没有外键时退回命名推断，不新增固定 SQL 模板。
- 已为标准评估报告接入 run trace 关联，每个 case 会写入 `run_id` 和 `run_detail_path`，便于从断言失败直接查看 `/api/runs/{run_id}`。
- 已增强模型 SQL Generator 上下文 smoke，prompt payload 可结构化测试，模型编造字段会在 Guard/Validator smoke 中被拦截。
- 已为标准评估报告增加 `run_trace_summary`，并聚合缺失表是否进入召回上下文，帮助区分 schema 召回不足和 SQL 生成不足。
- 已增强 Schema 主题表召回，用户、流量、优惠券相关问题会把 `users`、`traffic_events`、`coupons`、`coupon_usages` 纳入上下文。
- 已新增 SQL 关键上下文表覆盖检查，能诊断已召回非默认业务表是否进入最终 SQL；模型生成开启时可在 rewrite/确定性结果漏表后转向模型 cold path。
- 已新增专用意图识别模型适配，`question_intent_parser` 支持通过 `INTENT_*` 配置使用独立语义模型；本机 `backend/.env` 已创建占位项，真实密钥不提交。
- 已增强 SQL Generator prompt 的意图上下文和指标语义，结构化传入 `question_intent`，并明确总销售额、订单数、客单价口径；SQL 意图校验会拦截 `JOIN payments` 后直接 `SUM(orders.total_amount)` 的重复累计风险。
- 已新增后端开发者可观测性 V1：标准回归用例集、`/api/runs/{run_id}.debug_summary`、结构化 JSON 摘要日志、链路节点耗时统计和 `analysis_graph.pipeline_timings` run trace。

## 最近完成模块

### 1. 项目结构与 FastAPI 最小闭环

- commit: `8071783 初始化项目结构并通过前后端验证`
- 内容：
  - 创建 `frontend/` 和 `backend/`
  - FastAPI mock `/api/analyze`
  - 前端聊天式问答页
  - 根目录项目脚本
- 验证：
  - `npm run frontend:build`
  - `npm run backend:test`
  - `npm run test:e2e`

### 2. 指标口径后端 CRUD

- commit: `094ecf2 实现指标口径后端CRUD并通过测试`
- 内容：
  - `GET/POST/PUT/DELETE /api/metrics`
  - `MetricService`
  - 内存版 `MetricRepository`
  - `metric_definitions` migration
  - 前端指标页接入 `metricClient`
- 验证：
  - `npm run backend:test`，3 个测试通过
  - `npm run frontend:build`
  - `npm run test:e2e`

### 3. PostgreSQL 数据库与真实 Olist 数据基础

- commit: 本模块已提交并推送，提交信息为 `建立PostgreSQL数据基础并导入真实Olist数据`。具体 hash 以 `git log --oneline -1` 为准。
- 内容：
  - 创建本地 `backend/.env`，使用本机可连接 PostgreSQL 账号指向 `local_data_agent`；真实密码只保存在本机 `.env`，不写入文档。
  - 添加 PostgreSQL 连接、migration runner、Olist 下载脚本、Olist 导入脚本、metadata seed 和数据库检查脚本
  - 创建业务表：`users`, `products`, `orders`, `order_items`, `payments`, `refunds`, `reviews`, `traffic_events`, `coupons`, `coupon_usages`, `inventory_snapshots`, `product_costs`
  - 创建 Agent 元数据表：`schema_metadata`, `metric_definitions`, `sql_memories`, `query_runs`, `tool_calls`, `embedding_documents`
  - 已下载真实 Olist CSV，并导入 PostgreSQL
- 数据行数：
  - `users`: 99,441
  - `products`: 32,951
  - `orders`: 99,441
  - `order_items`: 112,650
  - `payments`: 103,886
  - `refunds`: 1,234
  - `reviews`: 98,410
  - `inventory_snapshots`: 32,951
  - `product_costs`: 32,951
  - `schema_metadata`: 78
  - `metric_definitions`: 4
- 验证：
  - `py -3 backend/scripts/init_db.py`
  - `py -3 backend/scripts/download_olist.py`
  - `py -3 backend/scripts/import_olist.py`
  - `py -3 backend/scripts/seed_metadata.py`
  - `py -3 backend/scripts/check_db.py`
  - `npm run backend:test`
  - `npm run test:e2e`
  - `npm run frontend:build`

### 4. 指标口径 PostgreSQL Repository

- commit: 本模块已提交并推送，提交信息为 `切换指标口径为PostgreSQL仓储并补全文档`。
- 内容：
  - 补充 DataGrip 连接说明：`docs/database-datagrip.md`
  - 补充 PostgreSQL 数据基础模块完成文档
  - 将 `MetricRepository` 从内存仓储切换为 PostgreSQL `metric_definitions` 表
  - 更新指标 CRUD 测试，使用唯一测试指标名避免冲突
- 验证：
  - `npm run backend:test`
  - `npm run test:e2e`
  - `npm run frontend:build`

### 5. SQL Guard / Validator

- commit: 本模块已提交并推送，提交信息为 `实现SQL Guard和Validator并通过测试`。
- 内容：
  - 新增 `SqlValidationRequest`, `SqlValidationResult`, `SqlGuardResult`
  - 新增 `validate_sql` 和 `guard_sql`
  - 使用 `sqlglot` 解析 PostgreSQL SQL
  - 覆盖只读、单语句、写操作拦截、白名单表、`SELECT *`、自动 LIMIT
- 验证：
  - `npm run backend:test`，12 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 6. 只读 SQL Executor

- commit: 本模块已提交并推送，提交信息为 `实现只读SQL Executor并通过测试`。
- 内容：
  - 新增 `SqlExecutionResult`
  - 新增 `execute_guarded_sql`
  - Executor 只接受 Guard 放行后的 `final_sql`
  - 支持 `success`、`blocked`、`error` 三种结果状态
  - 执行结果转为 JSON-friendly 行数据
- 验证：
  - `npm run backend:test`，15 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 7. `/api/analyze` 真实 SQL 垂直切片

- commit: `ae9f129 接入analyze真实SQL工具链并通过测试`
- 内容：
  - 新增 `analysis_graph.py`，固定销售趋势问题先走真实 SQL 模板
  - 新增 `analysis_presenter.py`，将真实查询结果转为 `AnalyzeResponse`
  - `AgentService` 从 mock graph 切换到真实 Guard + Executor graph
  - `/api/analyze` 现在返回真实 PostgreSQL 查询结果
- 验证：
  - `npm run backend:test`，15 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 8. Schema + Metric Retriever 最小切片

- commit: `9956194 接入Schema和指标检索并通过测试`
- 内容：
  - 新增 `MetricContext`、`SchemaColumnContext`、`RetrievalContext`
  - 新增 `metric_retriever.py`，从 PostgreSQL `metric_definitions` 召回相关指标口径
  - 新增 `schema_retriever.py`，从 PostgreSQL `schema_metadata` 召回相关表字段
  - 新增 `context_builder.py`，组合指标和 schema 上下文
  - `/api/analyze` 在 SQL Guard / Executor 前先构建检索上下文
  - `AnalyzeResponse.source` 中的指标口径、表、字段改由召回上下文生成
- 验证：
  - `npm run backend:test`，18 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 9. Query Run Logging 运行记录

- commit: 本模块已提交并推送，提交信息为 `实现Query Run日志落库并通过测试`。
- 内容：
  - 新增 `QueryRunRecord`、`QueryRunDetail`、`ToolCallRecord`
  - 新增 `RunRepository`、`RunService` 和 `QueryRunLogger`
  - 新增开发者调试接口 `GET /api/runs`、`GET /api/runs/{run_id}`
  - `/api/analyze` 每次运行写入 `query_runs`
  - 关键工具调用写入 `tool_calls`：上下文召回、SQL Guard、SQL Executor、结果整理
  - README 已更新当前能力、API 入口和开发约定
- 验证：
  - `npm run backend:test`，20 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 10. SQL Memory Retriever / Reuse Planner 最小切片

- commit: 本模块已提交并推送，提交信息为 `实现SQL Memory检索复用并通过测试`。
- 内容：
  - 新增 `SqlMemoryRecord`、`SqlMemoryCandidate`、`SqlReusePlan`、`SqlMemoryUpsert`
  - 新增 `SqlMemoryRepository`、`MemoryService` 和 `/api/memories` 调试接口
  - 新增 `retrieve_sql_memory`、`plan_sql_reuse`、`upsert_successful_sql_memory`
  - `/api/analyze` 会先检索 SQL Memory，再决定 `fast_path` 或 `cold_path`
  - 查询成功后写入或更新 `sql_memories`
  - `query_runs.memory_hit` 会记录是否命中历史 SQL
- 验证：
  - `npm run backend:test`，24 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 11. SQL Memory 参数化模板与时间范围改写

- commit: 本模块已提交并推送，提交信息为 `实现SQL Memory参数化模板并通过测试`。
- 内容：
  - 新增 `SalesTrendParameters`
  - 新增 `parse_sales_trend_parameters` 和 `render_sales_trend_sql`
  - `/api/analyze` 会从用户问题解析“最近 N 天”并渲染销售趋势 SQL
  - 高置信 SQL Memory 命中时会按当前问题重新渲染 SQL
  - `sql_memories.parameters` 写入 `days` 和 `granularity`
- 验证：
  - `npm run backend:test`，28 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 12. SQL Rewriter / Generator 最小切片

- commit: `2ca2874 实现SQL Rewriter最小切片并通过测试`
- 内容：
  - 新增 `GeneratedSql`
  - 新增 `generate_or_rewrite_sales_sql`
  - 扩展 `SalesTrendParameters`，支持 `granularity` 和 `metric`
  - 支持“最近 90 天每月订单数是多少？”生成月度订单数 SQL
  - `/api/analyze` 在 SQL Memory 规划后、Guard 前执行 SQL 生成/改写节点
  - `tool_calls` 新增 SQL 生成/改写工具调用记录
- 验证：
  - `npm run backend:test`，33 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 13. Top N 商品/品类销售额查询切片

- commit: 本模块已提交并推送，提交信息为 `实现TopN商品品类查询并通过测试`。
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `top_product_sales` 和 `top_category_sales`
  - 新增 `limit` 参数解析，支持“前 10 个商品”等 Top N 问法
  - 商品/品类问题自动召回 `order_items`、`products`、`payments` 相关 schema
  - `/api/analyze` 可执行商品销售额 Top N 和品类销售额排行真实 SQL
  - 聊天页结果表头调整为更通用的“维度 / 销售额”
- 验证：
  - `npm run backend:test`，38 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 14. 退款率 / 支付成功率查询切片

- commit: `ec677d3 实现退款率支付成功率查询并通过测试`
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `category_refund_rate`、`payment_success_rate`、`payment_failure_rate`
  - 支持“哪个商品品类退款率最高？”生成品类退款率 SQL
  - 支持“每个支付方式的成功率是多少？”生成支付方式成功率 SQL
  - 退款类问题自动召回 `refunds`、`order_items`、`products`、`payments` 相关 schema
  - Presenter 兼容 `refund_rate`、`success_rate`、`failure_rate` 结果列
- 验证：
  - `npm run backend:test`，43 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 15. 毛利率查询切片

- commit: `98322e7 实现毛利率查询并通过测试`
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `category_gross_margin`
  - 支持“最近 30 天毛利率最高的商品品类是什么？”生成品类毛利率 SQL
  - 毛利率问题自动召回 `order_items`、`products`、`product_costs`、`payments` 相关 schema
  - Presenter 兼容 `gross_margin` 结果列
- 验证：
  - `npm run backend:test`，46 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 16. 复购率 / 城市客单价查询切片

- commit: `d98f88c 实现复购率城市客单价查询并通过测试`
- 内容：
  - 扩展 `SalesTrendParameters.metric`，支持 `repeat_purchase_rate`、`city_avg_order_value`
  - 支持“最近 90 天复购率是多少？”生成整体复购率 SQL
  - 支持“每个城市的客单价是多少？”生成城市客单价 SQL
  - 用户维度问题自动召回 `users`、`orders`、`payments`、`refunds` 相关 schema
  - Presenter 兼容 `segment_label`、`city_label`、`repeat_rate` 结果列
- 验证：
  - `npm run backend:test`，51 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 17. Schema Metadata 自动同步

- commit: `ec5c0e1 实现Schema元数据自动同步并通过测试`
- 内容：
  - 新增 `SchemaSyncService`，从 PostgreSQL `information_schema.columns` 同步当前 `public` schema 的真实表字段
  - 新增 `backend/scripts/sync_schema_metadata.py`，用于换库、导入新表或字段变化后的手动刷新
  - 新增 `004_schema_metadata_unique.sql`，清理重复元数据并创建 `(table_name, column_name)` 唯一索引
  - `seed_metadata.py` 改为复用同步服务，减少重复 schema 写入逻辑
  - 新增 `test_schema_sync_service.py`，覆盖过滤、字段读取和 upsert 保留人工说明逻辑
- 验证：
  - `npm run backend:test`，54 个测试通过
  - `py -3 backend/scripts/init_db.py`
  - `py -3 backend/scripts/sync_schema_metadata.py`，同步 12 张表、78 个字段
  - `npm run test:e2e`
  - `npm run frontend:build`

### 18. 统一 ModelAdapter 基础层

- commit: `25ac0dc 实现统一ModelAdapter基础层并通过测试`
- 内容：
  - 扩展 `backend/app/core/config.py`，支持模型 provider、base URL、model、API key、timeout、retry 配置
  - 新增 `backend/app/core/model_adapter.py`，提供 OpenAI-compatible chat completions 统一入口
  - 支持结构化 `ModelRequest`、`ModelResponse`、`ModelUsage`，并把空消息、HTTP 错误、transport 异常转换为结构化错误
  - 支持可注入 transport，测试不依赖真实模型服务或真实 API key
  - 更新 `backend/.env.example`，只保留模型配置占位值
- 验证：
  - `npm run backend:test`，59 个测试通过

### 19. Model-backed SQL Generator 基础工具

- commit: `75a6627 实现模型SQL生成基础工具并通过测试`
- 内容：
  - 新增 `backend/app/tools/model_sql_generator.py`
  - 基于 `RetrievalContext` 和 `SqlReusePlan` 构造受控 prompt，只使用召回到的表字段和指标口径
  - 通过 `ModelAdapter.chat()` 调用 OpenAI-compatible 模型，要求 JSON response format
  - 解析模型响应为 `GeneratedSql`，新增 `model_generate`、`model_rewrite`、`model_error` 路径
  - 模型生成 SQL 当前不直接执行，后续接主链路时仍必须经过 Validator / Guard / Executor
  - 新增 `test_model_sql_generator.py`，覆盖 prompt、JSON 解析、warning、成功生成和模型错误路径
- 验证：
  - `npm run backend:test`，64 个测试通过

### 20. Model SQL Generator cold_path 配置开关接入

- commit: `5ab8b4f 接入模型SQL生成cold_path并通过测试`
- 内容：
  - 新增 `MODEL_SQL_GENERATOR_ENABLED` 配置，默认关闭模型 SQL 生成
  - `analysis_graph._select_generated_sql()` 负责集中选择 SQL 生成路径
  - 开启配置且 `reuse_plan.path_type == "cold_path"` 时调用 `generate_sql_with_model()`
  - 模型返回 SQL 后继续进入现有 SQL Guard 和只读 Executor
  - 模型失败或未返回 SQL 时回退 `generate_or_rewrite_sales_sql()`
  - 新增 `test_analysis_graph_sql_selection.py` 覆盖关闭、开启、回退和 rewrite_path 不调用模型
- 验证：
  - `npm run backend:test`，68 个测试通过

### 21. 标准问题评估集基础设施

- commit: `e8df5ae 建立标准问题评估集并通过测试`
- 内容：
  - 新增 `eval/datasets/standard_questions.jsonl`，包含 20 个 V1 标准问题
  - 新增 `eval/scripts/run_eval.py`，可逐条调用 `/api/analyze` 并生成评估报告
  - 新增 `eval/reports/latest_eval_report.json`，记录最近一次评估结果
  - 新增 `npm run eval:standard`
  - 新增 `test_eval_runner.py`，覆盖数据集读取和报告指标汇总
  - README 增加标准问题评估说明
- 验证：
  - `npm run backend:test`，70 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功

### 22. 标准问题评估断言增强

- commit: `375de27 增强标准问题评估断言并通过测试`
- 内容：
  - `EvalCaseResult` 新增 `missing_tables`、`missing_keywords`、`table_match`、`keyword_match`、`strict_ok`
  - 评估报告新增 `strict_success_count`、`strict_success_rate`、`table_match_rate`、`keyword_match_rate`、`assertion_failures`
  - CLI 输出新增严格成功率
  - 测试覆盖“链路成功但断言失败”的情况
  - README 增加评估指标解释
- 验证：
  - `npm run backend:test`，71 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功，严格成功率 55%

### 23. SQL Memory fast_path 表/意图约束

- commit: `6a12c25 增强SQLMemory复用约束并通过测试`
- 内容：
  - `SqlMemoryCandidate` 新增 `required_table_match` 和 `required_tables`
  - `retrieve_sql_memory()` 根据问题推断用户、流量、优惠券等关键表，并检查候选 SQL 是否包含这些表
  - `plan_sql_reuse()` 要求高分且关键表匹配才允许 `fast_path`
  - 缺少关键表的高分候选降级为 `rewrite_path`
  - 新增单元测试覆盖阻止错误 fast_path 和允许合法 fast_path
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功，严格成功率 55%，memory hit 从 100% 降到 60%

### 24. V1 核心文档补齐

- commit: `39ac317 补齐V1核心文档并通过验证`
- 内容：
  - 新增 `docs/architecture.md`，说明 V1 架构、产品边界和主链路。
  - 新增 `docs/data_model.md`，说明业务表、Agent 元数据表、迁移和指标口径。
  - 新增 `docs/agent_workflow.md`，说明 `/api/analyze` 的检索、记忆、SQL 选择、Guard、Executor、日志和记忆写入链路。
  - 新增 `docs/sql_guard.md`，说明 Validator、Guard、白名单表和只读 Executor。
  - 新增 `docs/sql_memory.md`，说明 SQL Memory 打分、fast_path 关键表约束和写入条件。
  - 新增 `docs/evaluation.md`，说明标准问题评估集、报告字段和当前基线。
  - README 增加 V1 核心文档入口。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run eval:standard`，20/20 链路执行成功，严格成功率 55%
  - `npm run test:e2e`
  - `npm run frontend:build`

### 25. V1 接口文档补齐

- commit: `2f62bc0 补齐V1中文接口文档并通过验证`
- 内容：
  - 新增 `docs/api.md`，按普通业务接口和开发者调试接口分层说明当前 API。
  - 覆盖 `GET /api/health`、`POST /api/analyze`、指标口径 CRUD、运行记录和 SQL Memory 调试接口。
  - 中文说明请求参数、响应字段、错误边界、接口用途和当前风险。
  - README 增加 `docs/api.md` 入口，并在 API 入口段落链接完整接口文档。
  - 本模块只更新文档，不修改后端接口、前端页面、数据库结构或 Agent 行为。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run test:e2e`
  - `npm run frontend:build`

### 26. 前后端接口映射文档

- commit: `8339e03 补齐前后端接口映射文档并通过验证`
- 内容：
  - 新增 `docs/api_frontend_mapping.md`，说明前端 API client、TypeScript 类型和后端接口的映射关系。
  - 记录 `analysisClient.ts`、`metricClient.ts` 当前调用的后端路径和页面入口。
  - 明确后端 `AnalyzeResponse.trace`、`AnalyzeResponse.steps` 当前未进入前端类型和普通用户页面。
  - README 和 `docs/api.md` 增加映射文档入口。
  - 本模块只更新中文文档，不修改前端、后端、数据库或 Agent 行为。
- 验证：
  - `npm run frontend:build`
  - `npm run backend:test`，73 个测试通过
  - `npm run test:e2e`

### 27. 接口错误码与权限边界文档

- commit: `5015999 补齐接口错误码权限文档并通过验证`
- 内容：
  - 新增 `docs/api_error_auth.md`，说明当前 API 错误响应、状态码、前端错误处理现状、权限边界和上线前检查清单。
  - README、`docs/api.md`、`docs/api_frontend_mapping.md` 增加该文档入口。
  - 明确当前没有登录鉴权层，`/api/runs` 和 `/api/memories` 属于开发者调试接口，不进入普通用户主导航。
  - 本模块只更新中文文档，不修改后端接口、前端错误展示、鉴权逻辑或数据库结构。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run frontend:build`
  - `npm run test:e2e`

### 28. 接口变更流程与版本维护文档

- commit: `5bfab1e 补齐接口变更流程文档并通过验证`
- 内容：
  - 新增 `docs/api_change_process.md`，说明 API 兼容变更、破坏性变更、同步清单、验证门槛、版本策略和回滚记录格式。
  - README、`docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_error_auth.md` 增加该文档入口。
  - 明确 V1 当前使用 `/api` 前缀和 `app_version=0.1.0`，暂不引入 `/api/v1` 路径。
  - 本模块只更新中文文档，不修改 API 实现、前端类型、测试代码或数据库结构。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run frontend:build`
  - `npm run test:e2e`

### 29. 接口联调与 Smoke 示例文档

- commit: `a1805e3 补齐接口联调Smoke文档并通过验证`
- 内容：
  - 新增 `docs/api_smoke_examples.md`，说明本地启动、PowerShell/curl 调用示例、自动 smoke 检查点、验证命令分层和常见问题。
  - README、`docs/api.md`、`docs/api_frontend_mapping.md`、`docs/api_error_auth.md`、`docs/api_change_process.md` 增加该文档入口。
  - 明确 `npm run test:e2e` 当前检查 `/api/health` 和一次 `/api/analyze` 最小链路，不等于完整标准问题评估。
  - 本模块只更新中文文档，不修改接口实现、测试脚本、前端 API client 或数据库结构。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run frontend:build`
  - `npm run test:e2e`

### 30. 接口文档索引与阅读顺序

- commit: `b479fa3 补齐接口文档索引并通过验证`
- 内容：
  - 新增 `docs/api_index.md`，说明接口文档阅读顺序、角色路径、文档职责表和维护规则。
  - README 和所有接口主题文档增加索引入口。
  - 明确接口文档覆盖范围和当前不代表的能力，例如未实现登录鉴权、未引入 `/api/v1`。
  - 本模块只更新中文文档，不修改接口实现、前端 API client、测试脚本或数据库结构。
- 验证：
  - `npm run backend:test`，73 个测试通过
  - `npm run frontend:build`
  - `npm run test:e2e`

### 31. 统一前端 API Client 与错误解析

- commit: `9f65042 统一前端APIClient并通过验证`
- 内容：
  - 新增 `frontend/src/api/client.ts`，统一 base URL、JSON 请求体、响应解析和 FastAPI `detail` 错误解析。
  - `analysisClient.ts` 和 `metricClient.ts` 改为复用 `apiRequest<T>()`，不再分散直接调用 `fetch`。
  - 错误提示保持中文业务表达，`500` 和网络异常不会暴露数据库、模型、SQL Memory 或调试 payload。
  - 更新 `docs/api_frontend_mapping.md`、`docs/api_error_auth.md`、README、计划文档和模块完成说明。
- 验证：
  - `npm run frontend:build` 已通过
  - `npm run backend:test`，73 passed，1 个 `StarletteDeprecationWarning`
  - `npm run test:e2e` 已通过

### 32. 数据问答通用 Rows 契约

- commit: `107b699 实现数据问答通用Rows并通过验证`
- 内容：
  - `backend/app/schemas/analysis.py` 将 `AnalysisRow` 从固定销售字段改为通用字典行。
  - `analysis_presenter.py` 保留内部总结逻辑，但响应 `rows` 改为 SQL Executor 的真实结果列。
  - `frontend/src/types/analysis.ts` 改为 `Record<string, string | number | boolean | null>`。
  - `ChatPage.tsx` 改为根据返回行动态生成最多 6 列结果表，并对常见列名做中文化和数字格式化。
  - 更新接口文档、前后端映射、README、计划文档和模块完成说明。
- 验证：
  - `npm run frontend:build` 已通过
  - `npm run backend:test`，73 passed，1 个 `StarletteDeprecationWarning`
  - `npm run test:e2e` 已通过

### 33. 数据问答 Trace / Steps 前端类型契约

- commit: `ca1e343 补齐分析追踪前端类型并通过验证`
- 内容：
  - `frontend/src/types/analysis.ts` 新增 `AnalysisTrace` 和 `AgentStep`。
  - `AnalysisResponse` 声明后端已返回的 `trace` 和 `steps` 字段。
  - 普通聊天页继续不展示内部追踪细节。
  - `ChatPage.tsx` 将“本地 PostgreSQL / 只读执行”文案调整为“只读安全分析”，避免普通用户界面出现数据库状态感文案。
  - 更新接口映射、README、计划文档和模块完成说明。
- 验证：
  - `npm run frontend:build` 已通过
  - `npm run backend:test`，73 passed，1 个 `StarletteDeprecationWarning`
  - `npm run test:e2e` 已通过

### 34. 统一检索评分基础层

- commit: `6f62e90 统一检索评分基础层并通过验证`
- 内容：
  - 新增 `backend/app/tools/retrieval_scoring.py`，统一文本归一化、文档拼接、文本相似、关键词命中、集合重合和加权评分。
  - `metric_retriever.py` 复用共享评分工具，指标分由名称命中、关键词命中、文本相似和趋势意图组成。
  - `schema_retriever.py` 为字段增加 `score`，按必需字段、相关表、关键词、文本相似和字段优先级排序。
  - `sql_memory_tools.py` 复用共享文本相似和集合重合分，原 SQL Memory 混合公式保持不变。
  - 新增 `test_retrieval_scoring.py`，并增强检索相关测试。
- 验证：
  - `npm run backend:test`，80 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过

### 35. EmbeddingAdapter 基础层

- commit: `cd840d0 实现EmbeddingAdapter基础层并通过验证`
- 内容：
  - `backend/app/core/config.py` 新增 embedding provider、base URL、model、API key、dimension、timeout、retry 配置。
  - 新增 `backend/app/core/embedding_adapter.py`，支持 OpenAI-compatible `/embeddings` 调用。
  - 支持 `deterministic` provider，本地开发和测试无外部服务时可生成稳定向量。
  - 新增结构化 `EmbeddingRequest`、`EmbeddingResponse`、`EmbeddingUsage`，并把空输入、HTTP 错误、transport 异常转换为结构化错误。
  - 更新 `backend/.env.example`，只保留 embedding 占位配置。
  - 新增 `backend/tests/test_embedding_adapter.py` 覆盖 payload、鉴权、错误和 deterministic fallback。
- 验证：
  - `npm run backend:test`，87 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过

### 36. Schema / Metric Embedding 同步

- commit: 本模块随本次提交推送完成，提交信息为 `实现SchemaMetric向量同步并通过验证`。
- 内容：
  - 新增 `backend/app/services/embedding_sync_service.py`，从 `schema_metadata` 和启用状态的 `metric_definitions` 构造中文检索文档。
  - 统一调用 `EmbeddingAdapter` 生成向量，避免各处散落 embedding provider 调用。
  - 通过 `%s::vector` 回写 `schema_metadata.embedding` 和 `metric_definitions.embedding`。
  - 新增 `backend/scripts/sync_embeddings.py`，支持 `--target all|schema|metric`。
  - 新增 `backend/tests/test_embedding_sync_service.py`，覆盖文档构造、向量 literal、JSON 容错、schema/metric 写入和失败不中断。
  - 更新 README、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_embedding_sync_service.py`，7 passed
  - `npm run backend:test`，94 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 37. pgvector 混合检索接入

- commit: 本模块随本次提交推送完成，提交信息为 `接入pgvector混合检索并通过验证`。
- 内容：
  - 新增 `backend/app/tools/vector_retrieval.py`，统一用 `EmbeddingAdapter` 生成问题向量并查询 pgvector 候选。
  - `metric_retriever.py` 将 `metric_definitions.embedding` 语义候选分纳入指标总分。
  - `schema_retriever.py` 将 `schema_metadata.embedding` 语义候选表并入加载范围，并将字段语义分纳入排序。
  - `retrieval.py` 为 `MetricContext` 和 `SchemaColumnContext` 增加内部 `semantic_score`，普通用户响应不展示该字段。
  - 新增 `backend/tests/test_vector_retrieval.py`，扩展 `test_retrieval_scoring.py`。
  - 更新 README、Agent 工作流、数据模型、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_vector_retrieval.py backend/tests/test_retrieval_scoring.py backend/tests/test_retrieval_tools.py`，17 passed
  - `npm run backend:test`，101 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 38. SQL Memory Embedding 混合检索

- commit: 本模块随本次提交推送完成，提交信息为 `接入SQLMemory向量检索并通过验证`。
- 内容：
  - `SqlMemoryUpsert` 增加 `question_embedding` 和 `sql_embedding`。
  - `SqlMemoryRepository` 在新增和更新 SQL Memory 时写入 `question_embedding` / `sql_embedding`。
  - `sql_memory_tools.upsert_successful_sql_memory()` 调用 `EmbeddingAdapter` 为问题和最终 SQL 生成向量。
  - `vector_retrieval.py` 新增 `retrieve_sql_memory_vector_candidates()`，查询 `sql_memories.question_embedding`。
  - `retrieve_sql_memory()` 优先用 pgvector 候选分填充 `semantic_similarity`，无候选时回退文本相似。
  - 更新 README、SQL Memory 文档、Agent 工作流、数据模型、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_sql_memory_tools.py backend/tests/test_vector_retrieval.py`，15 passed
  - `npm run backend:test`，106 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 39. SQL Memory 历史向量补齐

- commit: 本模块随本次提交推送完成，提交信息为 `补齐SQLMemory历史向量同步并通过验证`。
- 内容：
  - `EmbeddingSyncService` 新增 `sync_sql_memory_embeddings()`，扫描 `question_embedding IS NULL OR sql_embedding IS NULL` 的历史 memory。
  - 为 `canonical_question` 和 `final_sql` 生成两个向量，并写回 `sql_memories.question_embedding` / `sql_memories.sql_embedding`。
  - `backend/scripts/sync_embeddings.py` 的 `--target` 支持 `memory`，默认 `all` 包含 schema、metric、memory。
  - `backend/tests/test_embedding_sync_service.py` 覆盖 memory 扫描、双文本 embedding、双向量写入和失败不中断。
  - 更新 README、SQL Memory 文档、数据模型、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_embedding_sync_service.py`，10 passed
  - `npm run backend:test`，109 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 40. 通用分析结果 Presenter

- commit: 本模块已提交并推送，提交信息为 `实现通用分析结果Presenter并通过验证`。
- 内容：
  - `analysis_presenter.py` 新增 `ResultProfile` 和通用结果画像 helper。
  - 根据 SQL Executor 返回的真实列识别维度列、数值列和比例列。
  - `AnalyzeResponse.summary` 和 `metrics` 改为基于真实返回列动态生成，不新增 API 字段。
  - 保留既有销售、订单、商品、品类、退款率、支付成功率、毛利率、复购率、城市客单价摘要关键词。
  - 清理旧 `_summary_text()` / `_row_label()` 死代码，避免后续维护出现两套总结逻辑。
  - 新增 `backend/tests/test_analysis_presenter.py`，覆盖任意列结果和既有业务列结果。
  - 更新 README、Agent 工作流、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_analysis_presenter.py backend/tests/test_api.py`，12 passed，1 个 `StarletteDeprecationWarning`
  - `npm run backend:test`，111 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 41. 数据上下文刷新命令

- commit: 本模块随本次提交推送完成，提交信息为 `新增数据上下文刷新命令并通过验证`。
- 内容：
  - 新增 `ContextRefreshService`，按顺序同步 `schema_metadata` 和 embedding 检索资产。
  - 新增 `backend/scripts/refresh_context.py`，支持 `--include-table`、`--exclude-table`、`--skip-embeddings` 和 `--embedding-target`。
  - `package.json` 新增 `npm run context:refresh`。
  - 新增 `backend/tests/test_context_refresh_service.py`，覆盖默认全量刷新、跳过 embedding、指定 target 和非法 target。
  - 更新 README、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_context_refresh_service.py`，4 passed
  - `npm run backend:test`，115 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `py -3 backend/scripts/refresh_context.py --help` 已通过
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 42. Embedding 同步限量参数

- commit: 本模块随本次提交推送完成，提交信息为 `新增Embedding同步限量参数并通过验证`。
- 内容：
  - `EmbeddingSyncService` 的 schema、metric、memory 和 all 同步入口新增 `limit` 参数。
  - schema、metric、memory 读取 SQL 会用参数化 `LIMIT %s` 控制本次扫描数量。
  - `sync_embeddings.py` 新增 `--limit` 参数。
  - `refresh_context.py` 和 `ContextRefreshService` 新增 `--embedding-limit` / `embedding_limit`。
  - 新增 focused tests，覆盖 limit 归一化、SQL 参数化和 context refresh 透传。
- 验证：
  - `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，19 passed
  - `py -3 backend/scripts/sync_embeddings.py --help` 已通过
  - `py -3 backend/scripts/refresh_context.py --help` 已通过
  - `npm run backend:test`，120 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 43. Embedding 同步批量请求

- commit: 本模块随本次提交推送完成，提交信息为 `新增Embedding同步批量请求并通过验证`。
- 内容：
  - `EmbeddingSyncService` 的 schema、metric、memory 和 all 同步入口新增 `batch_size` 参数。
  - schema/metric 同步会按文档 batch 调用 `EmbeddingAdapter.embed()`。
  - SQL Memory 同步会按“问题 + SQL”成对 batch，并按返回向量顺序写回。
  - `sync_embeddings.py` 新增 `--batch-size` 参数。
  - `refresh_context.py` 和 `ContextRefreshService` 新增 `--embedding-batch-size` / `embedding_batch_size`。
  - 新增 focused tests，覆盖批量写回、memory 成对向量、短响应失败和 context refresh 透传。
- 验证：
  - `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，25 passed
  - `py -3 backend/scripts/sync_embeddings.py --help` 已通过
  - `py -3 backend/scripts/refresh_context.py --help` 已通过
  - `npm run backend:test`，126 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 44. Embedding 批量失败单条重试

- commit: 本模块随本次提交推送完成，提交信息为 `新增Embedding批量失败单条重试并通过验证`。
- 内容：
  - `EmbeddingSyncService` 的 schema、metric、memory 和 all 同步入口新增 `retry_single_on_batch_failure`，默认开启。
  - schema batch 失败后会单条重试，并只记录真正失败的字段。
  - metric batch 失败后会单条重试，并只记录真正失败的指标。
  - SQL Memory batch 失败后会按单条 memory 的问题/SQL 成对重试。
  - `ContextRefreshService` 透传重试开关。
  - 新增 focused tests，覆盖 schema、metric、memory 的 batch 失败单条重试和 context refresh 透传。
- 验证：
  - `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，28 passed
  - `npm run backend:test`，129 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 45. Embedding 同步批次限速

- commit: 本模块随本次提交推送完成，提交信息为 `新增Embedding同步批次限速并通过验证`。
- 内容：
  - `EmbeddingSyncService` 的 schema、metric、memory 和 all 同步入口新增 `sleep_ms`，默认 0。
  - 同步服务支持注入 `sleeper`，测试无需真实等待。
  - batch 之间会按 `sleep_ms` 等待；batch 失败后的单条重试也会按 `sleep_ms` 等待。
  - `sync_embeddings.py` 新增 `--sleep-ms` 参数。
  - `refresh_context.py` 和 `ContextRefreshService` 新增 `--embedding-sleep-ms` / `embedding_sleep_ms`。
  - 新增 focused tests，覆盖 sleep 参数、批次间等待、单条重试等待和 context refresh 透传。
- 验证：
  - `py -3 -m pytest backend/tests/test_embedding_sync_service.py backend/tests/test_context_refresh_service.py`，32 passed
  - `py -3 backend/scripts/sync_embeddings.py --help` 已通过
  - `py -3 backend/scripts/refresh_context.py --help` 已通过
  - `npm run backend:test`，133 passed，1 个 `StarletteDeprecationWarning`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%

### 46. 评估断言失败聚合诊断

- commit: `新增评估断言失败聚合诊断并通过验证`，已推送到 `origin/main`。
- 内容：
  - `eval/scripts/run_eval.py` 新增 `assertion_failure_summary`。
  - 聚合链路成功但严格断言失败案例的缺失表、失败类别、失败路径和 case id。
  - 新增 `_assertion_failure_summary()` 和 `_sorted_count_items()` 纯函数。
  - `backend/tests/test_eval_runner.py` 覆盖缺失表、类别、路径聚合。
  - 更新评估文档、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_eval_runner.py`，4 passed，1 个 `StarletteDeprecationWarning`
  - `npm run backend:test`，134 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%，报告已生成 `assertion_failure_summary`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 47. Schema 表关系上下文

- commit: `新增Schema表关系上下文并通过验证`，已推送到 `origin/main`。
- 内容：
  - `RetrievalContext` 新增后端内部 `table_relationships`。
  - 新增 `TableRelationshipContext`，描述左右表字段、关系类型、置信度和推断原因。
  - `context_builder.infer_table_relationships()` 基于同名 ID 字段和 `table.id` 到 `<singular_table>_id` 的通用约定推断 join hints。
  - `model_sql_generator` prompt 增加 `table_relationships`，跨表查询优先使用高置信关系。
  - 更新 README、Agent 工作流、数据模型、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_retrieval_tools.py backend/tests/test_model_sql_generator.py`，10 passed
  - `npm run backend:test`，135 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 48. SQL Validator 字段存在性校验

- commit: `接入SQL字段存在性校验并通过验证`，已推送到 `origin/main`。
- 内容：
  - `SqlValidationRequest` 新增可选 `schema_fields`。
  - `validate_sql()` 默认从 `schema_metadata` 加载 SQL 涉及表的字段集合。
  - Validator 支持校验单表未限定字段、JOIN 表别名字段和输出别名。
  - `schema_metadata` 不可用时降级 warning，不中断基础只读安全校验。
  - 更新 SQL Guard 文档、README、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_sql_validation_tools.py backend/tests/test_sql_execution_tools.py`，13 passed
  - `py -3 -m pytest backend/tests/test_sql_validation_tools.py backend/tests/test_sql_execution_tools.py backend/tests/test_api.py::test_analyze_supports_repeat_purchase_rate_slice`，14 passed，1 个 `StarletteDeprecationWarning`
  - `npm run backend:test`，139 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 49. Schema 字段业务含义提示

- commit: `增强Schema字段业务含义提示并通过验证`，已推送到 `origin/main`。
- 内容：
  - `SchemaSyncService` 新增字段名启发式说明生成。
  - 新增 `infer_schema_description()` 和 `infer_schema_business_meaning()`。
  - 支持常见字段类型：主键、外键、时间、状态、金额、数量、比例、地域、分类、名称、评分和文本说明。
  - `schema_metadata` upsert 继续保留已有人工说明，只补齐空说明字段。
  - 更新 README、数据模型文档、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_schema_sync_service.py backend/tests/test_embedding_sync_service.py`，33 passed
  - `npm run backend:test`，141 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 50. Schema 历史泛化说明刷新

- commit: `新增Schema历史泛化说明刷新并通过验证`，已推送到 `origin/main`。
- 内容：
  - `SchemaSyncService.sync_public_schema()` 新增 `refresh_generated_descriptions`。
  - `ContextRefreshService.refresh()` 透传 `refresh_generated_descriptions`。
  - `sync_schema_metadata.py` 新增 `--include-table`、`--exclude-table` 和 `--refresh-generated-descriptions`。
  - `refresh_context.py` 新增 `--refresh-generated-descriptions`。
  - 默认不覆盖非空说明；显式开启时只替换已知旧自动生成说明。
  - 更新 README、数据模型文档、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_schema_sync_service.py backend/tests/test_context_refresh_service.py`，10 passed
  - `py -3 backend/scripts/sync_schema_metadata.py --help` 已通过
  - `py -3 backend/scripts/refresh_context.py --help` 已通过
  - `npm run backend:test`，142 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 51. 运行日志上下文诊断增强

- commit: `增强运行日志上下文诊断并通过验证`，已推送到 `origin/main`。
- 内容：
  - `context_builder.build_retrieval_context` 工具调用输出增加 `relationship_count`、`tables` 和 `fields_sample`。
  - `analysis_graph.select_generated_sql` 工具调用输出增加 `has_sql`、`warning_count` 和 `warnings`。
  - `sql_validation_tools.guard_sql` 工具调用输出增加 warning/error 数量和样例。
  - 更新 runs 测试、Agent 工作流文档、API 文档、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_runs.py`，3 passed，1 个 `StarletteDeprecationWarning`
  - `npm run backend:test`，142 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 52. PostgreSQL 外键表关系上下文

- commit: `接入PostgreSQL外键关系上下文并通过验证`，已推送到 `origin/main`。
- 内容：
  - `build_retrieval_context()` 调用 `infer_table_relationships(..., include_database_foreign_keys=True)`。
  - `context_builder._load_postgres_foreign_key_relationships()` 从 PostgreSQL `information_schema` 读取真实外键。
  - 真实外键以 `relationship_type = foreign_key` 写入 `RetrievalContext.table_relationships`，置信度高于命名推断。
  - 数据库元数据不可用、没有外键或外键字段未被召回时，自动退回现有命名推断。
  - 更新 README、Agent 工作流、数据模型、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_retrieval_tools.py`，8 passed
  - `npm run backend:test`，145 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 53. 评估报告 Run Trace 关联

- commit: `新增评估RunTrace关联并通过验证`，已推送到 `origin/main`。
- 内容：
  - `EvalCaseResult` 新增 `run_id` 和 `run_detail_path`。
  - `analyze_with_test_client()` 在 `/api/analyze` 后读取 `/api/runs?limit=5`，匹配当前问题最近运行记录。
  - `eval/reports/latest_eval_report.json` 的 `cases`、`failures`、`assertion_failures` 均可携带 run trace 字段。
  - 更新 README、评估文档、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_eval_runner.py`，6 passed，1 个 `StarletteDeprecationWarning`
  - `npm run backend:test`，147 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - 抽查 `eval/reports/latest_eval_report.json`：20 个 case 均包含 `run_id` 和 `run_detail_path`，9 个断言失败项均包含 `run_id`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 54. 模型 SQL Generator 上下文 Smoke

- commit: `增强模型SQL生成上下文Smoke并通过验证`，已推送到 `origin/main`。
- 内容：
  - `model_sql_generator.build_sql_generation_payload()` 把模型 prompt payload 抽成结构化函数。
  - `_user_prompt()` 复用结构化 payload 后序列化为 JSON，模型调用协议不变。
  - `test_model_sql_generator.py` 覆盖指标口径、schema 字段、表关系、复用计划和 Validator/Guard 要求进入 payload。
  - 新增模型编造字段 smoke，确认 `orders.not_exists` 会在执行前被 Guard/Validator 拦截。
  - 更新 README、架构文档、Agent 工作流、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py`，11 passed
  - `npm run backend:test`，149 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 55. 评估 Run Trace 摘要诊断

- commit: `新增评估RunTrace摘要诊断并通过验证`，已推送到 `origin/main`。
- 内容：
  - `EvalCaseResult` 新增 `run_trace_summary`。
  - `analyze_with_test_client()` 读取 `/api/runs/{run_id}` 并提取工具调用摘要。
  - `_build_run_trace_summary()` 提取召回表、字段样例、关系数、SQL 生成路径、Guard warning/error 和 SQL Memory 规划。
  - `assertion_failure_summary` 新增 `by_missing_table_context_status`，区分缺失表是否进入过上下文。
  - 更新 README、评估文档、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_eval_runner.py`，8 passed，1 个 `StarletteDeprecationWarning`
  - `npm run backend:test`，151 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - 抽查 `eval/reports/latest_eval_report.json`：20 个 case 均包含 `run_trace_summary`；断言失败聚合显示 `users` 有 3 次未召回、1 次已召回但 SQL 未使用，`traffic_events` 3 次未召回，`coupon_usages` 2 次未召回，`coupons` 1 次未召回
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 56. Schema 主题表召回增强

- commit: `增强Schema主题表召回并通过验证`，已推送到 `origin/main`。
- 内容：
  - `schema_retriever.py` 新增 `SCHEMA_TOPIC_TABLES`，集中维护业务主题词到相关表的映射。
  - `_related_tables()` 改为遍历主题表规则，保留指标依赖表优先和 `orders` 默认兜底。
  - 增强用户、流量、优惠券主题召回，覆盖 `users`、`traffic_events`、`coupons`、`coupon_usages`。
  - `test_retrieval_tools.py` 新增流量、优惠券、新增用户和 Top 用户召回测试。
  - 更新 README、Agent 工作流、评估文档、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_retrieval_tools.py`，12 passed
  - `npm run backend:test`，155 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - 抽查 `eval/reports/latest_eval_report.json`：当前断言失败中的 `users`、`traffic_events`、`coupons`、`coupon_usages` 均为 `present_in_context`
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 57. SQL 关键上下文表覆盖检查

- commit: `0c68f9b 新增SQL上下文表覆盖检查并通过验证`，已推送到 `origin/main`。
- 内容：
  - `analysis_graph._context_table_coverage()` 从召回上下文和最终 SQL 中计算关键表覆盖情况。
  - 当前只把非默认业务表作为强覆盖要求，避免把基础订单/支付/商品表误判为必须全部出现在每条 SQL 中。
  - `_select_generated_sql()` 在确定性 SQL 漏掉关键上下文表时写入 warning；模型 SQL Generator 开启时，会尝试转为模型 cold path 重新生成。
  - `analysis_graph.select_generated_sql` 工具调用输出新增 `context_table_coverage`，包含 `required_tables`、`sql_tables`、`missing_tables`、`covered`。
  - 更新 README、Agent 工作流、评估说明、计划文档和模块完成说明。
- 验证：
  - `py -3 -m pytest backend/tests/test_analysis_graph_sql_selection.py`，7 passed
  - `npm run backend:test`，158 passed，1 个 `StarletteDeprecationWarning`
  - `npm run eval:standard`，20/20 链路成功，严格成功率 55%
  - `npm run frontend:build` 已通过
  - `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`

### 58. 专用意图识别模型适配

- commit: `接入专用意图识别模型配置`，已推送到 `origin/main`。
- 内容：
  - 新增 `INTENT_PARSER_ENABLED` 和 `INTENT_MODEL_*` 配置，允许意图识别模型和 SQL 生成模型分开部署。
  - `question_intent_parser` 优先使用专用意图模型配置；未配置时回退到 `MODEL_*`，模型失败时保留本地启发式兜底。
  - 移除上一轮针对单个口语 case 的意图维度清洗和核心汇总 SQL 强制覆盖。
  - `backend/.env.example` 增加意图模型配置示例。
  - 本机 `backend/.env` 已创建 `INTENT_*` 占位配置，真实值由用户自行填写且不提交。
  - 新增计划文档和模块完成文档：`docs/plans/2026-07-06-intent-model-adapter.md`、`docs/modules/2026-07-06-intent-model-adapter.md`。
- 验证：
  - `.venv\Scripts\python -m pytest backend\tests\test_question_intent_parser.py backend\tests\test_model_sql_generator.py backend\tests\test_analysis_graph_sql_selection.py`，38 passed

### 59. 意图上下文 Prompt 与聚合口径修正

- commit: 本模块随本次提交并推送，提交信息为 `增强意图上下文Prompt和聚合校验`。
- 内容：
  - `model_sql_generator` 的 prompt payload 新增 `question_intent` 和 `metric_semantics`，将意图模型解析出的指标、维度、时间范围、置信度传给 SQL 生成模型。
  - 明确 `sales_amount`、`order_count`、`avg_order_value` 的订单粒度口径，要求“总共卖了多少”和“平均卖了多少”分开输出。
  - prompt 明确要求 JOIN `payments` 后不能直接重复汇总 `orders.total_amount`，必须先按订单去重或先聚合支付表。
  - `analysis_graph` 将 `question_intent` 透传给模型 SQL 生成和 repair 请求。
  - SQL 意图校验新增重复聚合风险拦截，识别 `JOIN payments` 后直接 `SUM(o.total_amount)` 的 SQL 并触发 repair。
  - 启发式兜底新增“平均卖了多少钱 / 平均卖了多少”到 `avg_order_value` 的映射，并对模型失败下的复杂多指标问题更保守地反问。
  - 新增计划文档和模块完成文档：`docs/plans/2026-07-06-intent-context-prompt-and-aggregation.md`、`docs/modules/2026-07-06-intent-context-prompt-and-aggregation.md`。
- 验证：
  - `.venv\Scripts\python -m pytest backend\tests\test_question_intent_parser.py backend\tests\test_model_sql_generator.py backend\tests\test_analysis_graph_sql_selection.py`，42 passed

### 60. 后端可观测性与标准回归用例 V1

- commit: 本模块随本次提交并推送，提交信息为 `增强后端可观测性和回归用例`。
- 内容：
  - 新增 `eval/datasets/regression_questions.jsonl`，沉淀聚合口径、支付口径、安全校验和意图澄清回归问题。
  - `eval/scripts/run_eval.py` 支持 `forbidden_keywords`、`load_regression_cases()`、`forbidden_match_rate` 和 `by_forbidden_keyword` 聚合。
  - `QueryRunDetail` 新增 `debug_summary`，`RunService` 从 tool calls 汇总 run、memory、context、SQL generation、intent validation、Guard、Execution 和 timings。
  - `query_runs.user_question` 保留原始用户问题，`rewritten_question` 保存意图归一化后的问题。
  - `QueryRunLogger` 输出 `backend.observability` JSON 摘要日志，不记录完整 prompt 或 API key。
  - `analysis_graph` 记录节点耗时，并新增 `analysis_graph.pipeline_timings` tool call。
  - 新增 focused tests：runs 调试摘要、eval forbidden 断言、结构化日志、pipeline timing。
- 验证：
  - `.venv\Scripts\python -m pytest backend\tests\test_runs.py backend\tests\test_eval_runner.py backend\tests\test_analysis_graph_sql_selection.py backend\tests\test_run_logger.py`，42 passed，1 warning
  - `npm run backend:test`，170 passed，3 failed，1 warning。失败项均在 `backend/tests/test_api.py`，原因是当前本地未跟踪 `backend/tests/conftest.py` 的旧 fixture SQL 会触发重复聚合校验，返回空 SQL；生产校验未放宽。

## 当前架构边界

- React 只通过 `frontend/src/api/` 调 FastAPI。
- FastAPI API 层保持薄层。
- 业务逻辑放在 `services/`。
- Agent 编排放在 `agents/`。
- 确定性工具放在 `tools/`。
- 数据库访问后续放在 `db/repositories/`。
- 数据库结构必须放在 `backend/app/db/migrations/`。

## 当前正在做

“后端可观测性与标准回归用例 V1” 模块已完成代码、计划文档、模块文档、focused tests、commit 和 push。本机 `backend/.env` 仍只保留 `INTENT_*` 占位配置，真实密钥由用户填写且不提交。

## 下一步建议

按用户最新要求，不再继续堆固定 SQL 模板，优先推进换库、换表后仍能工作的通用能力：

1. 在真实本地模型可用后开启 `MODEL_SQL_GENERATOR_ENABLED=true` 跑标准评估，观察 `context_table_coverage.missing_tables` 是否下降。
2. 使用真实意图模型和 SQL 生成模型复测“2017年卖了多少钱，平均卖了多少钱”，确认生成 SQL 使用订单去重口径，标准结果应区分 `sales_amount` 和 `avg_order_value`。
3. 将 `eval/datasets/regression_questions.jsonl` 接入单独 npm script，例如 `npm run eval:regression`。
4. 修正当前本地未跟踪 `backend/tests/conftest.py` 中的旧 SQL fixture，使其先按订单去重或预聚合 payments，再恢复 `npm run backend:test` 全绿。
5. 为模型 SQL Generator 增加可选的离线 provider smoke，使用 fake adapter 覆盖用户、流量、优惠券跨表场景，不调用真实模型。
6. 继续处理 `present_in_context` 但 SQL 未使用的评估失败，优先改进模型 prompt、SQL 选择策略和通用验证，不新增固定 SQL 模板。

## 已知风险

- 指标 CRUD 已接入 PostgreSQL，但测试仍直接使用本地库，后续需要独立测试库。
- `/api/analyze` 已接入真实 Guard + Executor、schema/metric retriever、SQL Memory 和确定性 SQL Rewriter / Generator；通用 `rows` 和通用 Presenter 已完成，但 SQL 生成仍主要面向当前 V1 指标。
- ModelAdapter 基础层已完成，但 `/api/analyze` 尚未使用真实模型生成 SQL。
- Model SQL Generator 已接入 analysis graph 的 `cold_path` 尝试路径，但默认关闭，尚未用真实模型服务跑标准问题评估集。
- 模型 SQL Generator prompt payload 已有结构化 smoke，但真实模型输出质量仍未验证。
- 标准问题评估已可运行并区分严格断言；最近一次 20/20 链路成功，严格成功率 55%。当前主要失败表已进入上下文，剩余问题更偏 SQL 生成/复用策略。
- SQL 关键上下文表覆盖检查已能诊断漏表并在模型开启时尝试转向模型 cold path；默认模型关闭时仍只会记录 warning 和保留确定性 SQL。
- 重复聚合校验目前重点覆盖显式 `SUM(<orders alias>.total_amount)` 与 `payments` 同查的风险；更复杂的子查询和 CTE 仍需依赖模型 repair、Validator 和后续评估继续增强。
- 当前本地 `npm run backend:test` 仍有 3 个 `test_api.py` 失败，原因是未跟踪测试 fixture 返回的旧 SQL 被重复聚合校验拦截；focused tests 已通过，生产校验不应为旧 fixture 放宽。
- 评估报告已带 `run_id` / `run_detail_path`，但当前通过串行评估后查询最近 runs 匹配问题；如果未来并发评估，需要请求级 correlation id。
- 评估报告已带 `run_trace_summary`，但摘要依赖工具调用名称稳定；后续重命名工具需要同步 eval runner。
- EmbeddingAdapter 基础层、schema/metric embedding 同步、schema/metric pgvector 混合检索、SQL Memory embedding 写入和 question_embedding 检索已完成。
- schema/metric retriever 已接入 pgvector 语义候选，但真实质量依赖先运行 `sync_embeddings.py` 并配置真实 embedding provider。
- SQL Memory 新写入记录会带 question/sql embedding；旧记录可通过 `sync_embeddings.py --target memory` 补齐，未补齐时仍会回退文本相似。
- Schema Metadata 已支持自动同步字段结构，但尚未自动生成 embedding 或完整业务含义。
- `table_relationships` 已优先读取 PostgreSQL 外键，但用户库没有声明外键时仍只能依赖命名推断兜底。
- 销售趋势“最近 N 天”当前用最近 N 个有交易日期表达，不是严格自然日窗口；Top N 和复杂指标查询当前暂不带时间窗口。
- 支付成功率当前基于 `payments.status = 'paid'`，真实失败状态样本仍需后续数据增强。
- 毛利率当前基于合成 `product_costs.unit_cost`，后续可替换为真实成本口径。
- 复购率当前暂按全量已支付用户订单计算，未严格套用“最近 90 天”自然日窗口。
- `/api/runs` 是开发者调试接口，暂不放入普通用户主导航。
- `FastAPI TestClient` 当前有 `StarletteDeprecationWarning`，不影响功能，但后续可评估依赖版本。
- 用户最初提供的数据库用户名 `postgre` 认证失败；本机实际可用用户是 `postgres`。

## 每次继续开发前必须做

1. 读取本文件。
2. 读取相关 `docs/plans/*.md`。
3. 确认当前 git 状态。
4. 开发模块前创建或更新计划文档。
5. 模块完成后运行相关验证。
6. 更新本文件。
7. commit 并 push。

