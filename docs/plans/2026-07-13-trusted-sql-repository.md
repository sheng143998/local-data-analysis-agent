# Trusted SQL Repository

## Goal

将 SQL Memory 从“成功即复用”升级为可审计的候选库：仅 `verified` 记录可 fast path，其余记录仅作为生成参考；绑定语义契约和 schema 版本以防止口径或结构漂移误复用。

## Scope

- 新增 SQL Memory 生命周期状态、语义契约版本和 schema hash migration。
- 扩展 schema/repository/read API，新增安全的状态变更操作。
- 新写成功 SQL 标记为 `executed`；reuse planner 仅把 `verified` 作为 fast path。
- 旧记录迁移为 `reviewed`，可供模型参考但不可直接复用。

## Out of scope

- 不建立普通用户审批界面、不自动将模型成功 SQL 升级为 verified。
- 不放宽 Guard、QuerySpec 或 Executor，所有 verified SQL 仍经过现有校验。

## Implementation steps

- [ ] 定义状态契约、migration 与 repository 生命周期操作。
- [ ] 调整检索/reuse/写入策略并保留兼容读取。
- [ ] 测试 verified fast path、旧记录降级和状态变更。
- [ ] 后端全量、评测抽样、文档、commit、push。

## Validation plan

- SQL Memory focused tests、`npm.cmd run backend:test`、authenticated eval 抽样。

## Risks

- 旧 fast path 命中率会下降，这是用可靠性换取准确性；必须用评测报告解释。
- schema hash 初期只以显式版本字符串表达，完整自动 hash 由 Context Pack 模块完成。
