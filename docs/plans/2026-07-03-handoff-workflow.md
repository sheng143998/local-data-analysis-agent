# Handoff 工作流建立计划

Goal: 建立项目级 `docs/handoff/current.md`，并将“每次任务开始必须读取 handoff、模块结束必须更新 handoff”的规则落地到项目流程。

当前正在做：handoff 工作流已建立，文档变更已完成，准备提交并推送。

Scope:
- 包含：更新本地 skill、创建 handoff 文档、提交并推送流程文档。
- 不包含：业务功能代码变更。

Module boundary:
- Upstream inputs: 当前 git 提交、项目目录、最近模块完成状态。
- Downstream outputs: `docs/handoff/current.md` 和本模块计划。
- Likely touched files: `docs/handoff/current.md`, `docs/plans/2026-07-03-handoff-workflow.md`, `C:/Users/admin/.codex/skills/local-data-agent-dev-style/SKILL.md`。

Business logic:
- 每次继续开发前，先读 handoff，知道项目现在做到哪里。
- 每次模块完成后，更新 handoff，避免依赖聊天上下文。

Data contract:
- 本模块不新增 API 契约。
- Handoff contract: current status, latest commits, validation, next task, risks.

Implementation steps:
- [x] 读取并更新 skill
- [x] 创建 handoff 文档
- [x] 运行轻量验证
- [x] commit 并 push

Validation plan:
- `git status --short`
- 文档变更不需要前后端构建。

Risks and open questions:
- skill 文件在用户目录，不在项目 git 仓库内；项目仓库只能提交 handoff 与计划文档。
