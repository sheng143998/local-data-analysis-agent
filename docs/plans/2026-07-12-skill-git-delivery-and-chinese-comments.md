# Skill Git Delivery And Chinese Comments

## Goal

更新项目开发 Skill：每个通过验证的完整模块必须单独提交并推送；新写或修改的代码注释默认使用中文，并说明业务目的或业务约束。

## Scope

- 更新 `.agents/skills/local-data-analysis-development/SKILL.md` 的开发中和完成前规则。
- 明确模块完成后的 `git status`、提交和推送流程。
- 明确中文业务注释的适用边界，避免为显而易见语句添加无价值注释。

## Out Of Scope

- 不批量重写未触及代码中的历史英文注释。
- 不修改应用、数据库、前端接口或运行配置。
- 不替用户提交不属于当前模块的既有变更。

## Implementation Steps

- [x] 更新 Skill 的中文代码注释规范。
- [x] 更新 Skill 的模块验证后提交和推送规范。
- [x] 更新 handoff、创建模块记录并验证 Skill 内容。
- [x] 提交并推送本 Skill 模块（推送目标 `origin/main`；最终 hash 以 git log 为准）。

## Validation Plan

- UTF-8 读取 Skill、计划和 handoff。
- 检查 Skill 同时包含中文业务注释、模块验证、commit 和 push 的强制规则。
- 检查 git 工作区仅包含本 Skill 文档模块变更后再提交。

## Risks

- 自动提交必须排除用户的无关未提交变更，否则会把不相关工作混入模块提交。
- 中文注释要求不能替代清晰命名和分层；只对必要的业务规则、边界和决策写注释。
