# Trusted SQL Repository Foundation

## Completed behavior

- SQL Memory 增加 `candidate/executed/reviewed/verified/deprecated/rejected` 生命周期字段。
- 旧记录缺失状态时按 `reviewed` 读取；仅显式 `verified` 记录可进入 fast path。
- 新成功 SQL 持久化为 `executed`，不会自动成为可信复用资产。

## Validation

- SQL Memory 与分析图聚焦测试：`42 passed`。

## Remaining risks

- 管理员审核/提升为 verified 的接口和契约版本/schema hash 绑定仍待后续 Trusted SQL 管理模块。
- 本模块尚未运行全量后端和真实评测对照。
