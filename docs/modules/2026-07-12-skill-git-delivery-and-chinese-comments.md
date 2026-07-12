# Skill Git Delivery And Chinese Comments

## Completed Behavior

- 项目开发 Skill 现在要求新增或修改的代码注释默认使用中文，并说明业务目的、规则、安全边界或非显而易见的取舍。
- 完整模块在承诺验证通过后，必须检查 git 状态、只暂存本模块文件、创建独立提交并推送当前分支。
- 若存在无法安全拆分的用户无关变更，Skill 要求报告冲突，禁止静默混入提交。
- 模块记录和 handoff 必须记录 commit hash 与 push 结果；push 失败不能宣称模块已完整交付。

## Key Decisions

- 不强制为每一行代码添加注释；清晰命名和分层优先，注释只解释业务原因和边界。
- 不批量改写未触及的历史英文注释，避免无关 churn；后续修改所在代码时按新规则迁移。

## Validation

```powershell
Get-Content -Raw -Encoding UTF8 .agents/skills/local-data-analysis-development/SKILL.md
rg -n "中文|业务|提交|推送|git status" .agents/skills/local-data-analysis-development/SKILL.md
git status --short
```

- 已确认 Skill 包含 UTF-8 中文注释规则、验证后独立 commit/push 规则和无关变更隔离规则。
- commit: `完善模块提交推送与中文注释规范`（最终 hash 以 git log 为准）。
- push: `origin/main`，随该单模块提交执行；结果记录于当前 handoff 和交付回复。

## Remaining Risks

- Git 推送仍可能因远程权限、分支保护或网络失败而中断；Skill 要求显式报告而非跳过。
