# README 与展示文档刷新

## Completed behavior

- 更新 `README.md`，补充当前 Phase 0-7 交付状态、Semantic Contract、Clarification Policy、Query Plan、Trusted SQL、Inspector/Repair、Result Contract、Model Routing 和 authenticated 50-case 基线。
- 更新 `docs/architecture.md`，移除早期 mock 闭环描述，明确真实 PostgreSQL 主链路、分层边界、模型安全边界和质量状态。
- 更新 `docs/agent_workflow.md`，同步语义解析、澄清策略、Query Plan/Context Pack、Repair Rule、Result Contract 和任务角色路由。
- 更新 `docs/evaluation.md`，区分标准 20 题快速回归与 authenticated 50 题真值评测，补充 `新建 文本文档.txt` 对照、凭据边界、分批命令和可信基线。
- 更新 `docs/project-structure.md`，描述当前真实闭环、目录职责、交付流程和安全边界，不再写 mock 数据闭环。

## Key decisions

- 入口文档只引用聚合指标和报告路径，不写密码、模型密钥、完整 prompt、原始 SQL 或用户数据。
- `eval/reports/post_upgrade_full_eval.json` 是可信 50-case 对照；`eval/reports/latest_eval_report.json` 只作为标准 20 题本地工件，两者明确不可替代。
- 当前基线 `31/50` 执行、`13/50` 严格、`14/48` 答案匹配被明确标记为质量尚未达标，避免展示文档造成错误预期。

## API/data-contract impact

- 不修改 API、数据库 schema、运行代码、前端组件或评测结果。
- 仅更新 Markdown 文档、计划和 handoff；命令及路径均与当前仓库结构核对。

## Validation

- UTF-8 读取：README、架构、工作流、评估、项目结构、计划和 handoff 均通过。
- Markdown 相对链接校验：`MARKDOWN_LINKS_OK`。
- `git diff --check`：通过。
- 关键过期描述扫描：未发现 mock 闭环、旧 `157 passed` 或旧 `20/20` 结论。

## Remaining risks and follow-up

- 本机后端全量测试存在超时风险，文档已明确不把它写成全绿。
- 模型质量仍需使用稳定配置重跑 authenticated 50-case，并按失败分类继续改进。

## Delivery

- 提交：`c991e74`（`同步README与Agent展示文档`），已推送至 `origin/main`。
- 未跟踪/已修改的历史评测工件未纳入本次提交。
