# README 与展示文档刷新

## Goal

同步项目入口文档与当前已交付的复合数据分析 Agent 架构、评测基线、运行边界和开发入口，避免 README 与实现状态不一致。

## Scope

- 更新 `README.md`、`docs/architecture.md`、`docs/agent_workflow.md`、`docs/evaluation.md` 和 `docs/project-structure.md`。
- 展示 Semantic Contract、Clarification Policy、Trusted SQL、Query Plan/Context Pack、Inspector/Repair、Result Contract、Model Routing 和 authenticated 50-case 基线。
- 修正过期的 mock 闭环、固定模板、默认开关、旧测试数字和评估说明；保留 API 契约文档的独立边界。

## Out of scope

- 不修改应用代码、数据库迁移、API schema、前端组件或评测结果。
- 不提交 `backend/.env`、密码、模型密钥、原始 SQL、完整 prompt 或用户数据。
- 不把当前低质量基线包装成质量达标，也不伪造全量测试结果。

## Implementation steps

- [x] 创建计划并更新 handoff。
- [x] 更新五份展示文档，统一当前架构、命令、评估和安全边界。
- [x] 校验 Markdown 链接、命令路径、UTF-8 和 `git diff --check`。
- [x] 编写模块完成记录，更新 handoff，提交并推送。

## Validation plan

- 使用 PowerShell UTF-8 读取所有修改文档并检查关键路径存在。
- 扫描相对 Markdown 链接的目标文件，确认没有断链。
- 运行 `git diff --check`。
- 文档变更不运行后端全量测试；如发现命令或 API 描述变化，只做对应文档核对。

## Risks

- 评测报告可能被后续本地运行更新，文档必须明确可信 50-case 报告与标准 20-case 工件不可互相替代。
- 后端全量测试在本机存在超时风险，不能在文档中写成无条件全绿。
- README 属于入口文档，任何凭据、内部 prompt、原始工具 payload 和敏感结果都不得出现。
