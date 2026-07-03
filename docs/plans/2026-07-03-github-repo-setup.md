# GitHub 仓库与提交推送规则计划

Goal: 为本项目建立本地 git 仓库基础，写入模块完成后测试、提交、推送的交付规则，并在 GitHub 工具可用时创建远程仓库。

当前正在做：本地 git 仓库和首次提交已完成；GitHub 远程创建因缺少 `gh` 与 GitHub token 暂时阻塞。

Scope:
- 包含：更新 skill 交付规则、本地 git 初始化、忽略文件、README、首次验证与提交。
- 不包含：在缺少 GitHub CLI 或认证工具时强行创建远程仓库。

Module boundary:
- Upstream inputs: 当前项目文件、GitHub 交付要求、测试命令。
- Downstream outputs: 本地 git 仓库、首次提交、可推送的远程创建待办。
- Likely touched files: `C:/Users/admin/.codex/skills/local-data-agent-dev-style/SKILL.md`, `.gitignore`, `README.md`, `docs/plans/2026-07-03-github-repo-setup.md`。

Business logic:
- 每完成一个模块，先运行相关测试或 smoke check。
- 测试通过后提交一次聚焦 commit。
- 如果 GitHub 远程可用，立即 push。
- 如果 GitHub 工具或认证不可用，保留本地提交并明确阻塞原因。

Data contract:
- 本模块不新增 API 契约。
- Git contract: local commit -> remote push when GitHub auth is available.

Implementation steps:
- [x] 读取 GitHub skill 与项目 delivery skill
- [x] 将提交推送规则写入项目 skill
- [x] 初始化本地 git 仓库
- [x] 添加 `.gitignore` 和 README
- [x] 运行前端/后端验证
- [x] 创建首次 commit
- [x] 尝试创建 GitHub remote 或记录阻塞

Validation plan:
- `npm run frontend:build`
- `npm run backend:test`
- `npm run test:e2e`
- `git status --short`

Risks and open questions:
- 当前本机未安装 `gh`，也未发现可用 GitHub 创建仓库工具。
- `GITHUB_TOKEN` 和 `GH_TOKEN` 均未设置。
- 远程仓库创建和 push 需要 GitHub CLI、token 或其他认证工具。
