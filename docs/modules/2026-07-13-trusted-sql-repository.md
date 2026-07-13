# Trusted SQL Repository Foundation

## Completed behavior

- SQL Memory 增加 `candidate/executed/reviewed/verified/deprecated/rejected` 生命周期字段。
- 旧记录缺失状态时按 `reviewed` 读取；仅显式 `verified` 记录可进入 fast path。
- 新成功 SQL 持久化为 `executed`，不会自动成为可信复用资产。
- 管理员可通过 `PATCH /api/memories/{memory_id}/trust` 将审核结果显式更新为生命周期状态；只有 `verified` 可 fast path。

## Validation

- SQL Memory 与分析图聚焦测试：`42 passed`。
- Memory/API/reuse 回归：`21 passed, 1 warning`。

## Remaining risks

- 契约版本/schema hash 绑定仍待 Context Pack 自动 fingerprint 模块。
- 本模块尚未运行全量后端和真实评测对照。
