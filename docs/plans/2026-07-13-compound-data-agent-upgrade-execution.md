# Compound Data Agent Upgrade Execution

## Goal

执行已批准的复合数据分析 Agent 升级草案。以 authenticated ground truth benchmark 为质量门槛，按语义契约、澄清策略、可信 SQL、Query Plan 与 Context Pack、Inspector/Repair、Result Contract/Presenter、模型路由的顺序交付可独立验证和回滚的模块。

## Scope

- 配置并验证本机专用管理员评测账号，运行 50 条数据库真值集，建立首份可追踪基线。
- Phase 1：落地版本化 Semantic Contract、repository、migration 和开放式 Semantic Resolver。
- 后续阶段按草案建立独立计划、测试、模块记录和提交；允许无文件冲突的子任务并行探索或实现。

## Out of scope

- 不绕过 QuerySpec、SQL Guard、只读 Executor、用户会话归属或现有权限边界。
- 不把用户账号密码、数据库连接串、模型密钥或原始敏感结果提交到仓库。
- 不在未有评测和模块验证证据时一次性合并多个阶段的高风险改造。

## Implementation steps

- [x] 验证本地管理员账号，配置未跟踪的 `EVAL_AUTH_*`，生成并归档首份 50 case 基线。
- [x] 建立 Phase 1 Semantic Layer V2 的独立实施计划和数据模型。
- [x] 实现 Semantic Contract migration、repository、schema、resolver 与聚焦测试。
- [x] 以 benchmark 验证 Phase 1，记录模块、commit、push。
- [x] 依次执行 Phase 2 至 Phase 7 的实现、计划、模块记录、focused 验证和提交推送。

交付状态：Phase 1-7 的代码边界和文档已落地并推送。当前可信 50-case 对照为 `eval/reports/post_upgrade_full_eval.json`（执行 31/50、严格 13/50、答案 14/48）；`新建 文本文档.txt` 与 JSONL 真值集已核对 50/50、问题/答案差异 0。剩余工作是使用稳定模型配置重跑完整 authenticated benchmark 并按失败分类继续提升质量，不把当前低通过率宣称为质量达标。

## Validation plan

- 每个后端模块运行 focused pytest 与 `npm.cmd run backend:test`；接口或前端变更再运行 `npm.cmd run frontend:build`。
- 所有分析链路改动运行 authenticated `npm.cmd run eval:standard` 与 `npm.cmd run eval:database-baseline`。
- 记录执行成功率、严格 SQL 断言、答案匹配率、澄清指标、Guard 阻断和失败分类；不将配置错误混入质量统计。

## Risks

- 本地 SQL 模型延迟和输出波动会拉长真实基线，需要区分基础设施、模型、语义和 SQL 失败。
- 语义契约涉及业务口径，首批范围只覆盖已验证的基础实体和常用指标，未知明确概念必须保留开放式生成路径。
- 多 agent 并行只能处理边界不重叠的任务；迁移、核心 graph 与共享 schema 由主线统一合并和验证。
