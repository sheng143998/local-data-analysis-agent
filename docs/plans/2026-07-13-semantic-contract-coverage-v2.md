# Semantic Contract Coverage V2

## Goal

根据 authenticated 50-case 评测中的复杂聚合失败，补齐经过核对的业务语义契约，使意图、Query Plan、上下文和 SQL 模型收到一致的业务粒度、来源表字段、聚合与排序约束。

## Scope

- 为时间范围、商品与品类、退款与评价、用户地域与履约等稳定业务概念新增版本化契约。
- 让 Query Plan 从已解析的契约继承度量、维度、排序、限制和结果形态约束。
- 为 Resolver、Planner 和 SQL payload 添加回归测试，并用已配置管理员账号运行 authenticated 评测抽样。

## Out of scope

- 不在契约中保存可执行 SQL，不为单个题目写固定 SQL。
- 不修改 SQL Guard、只读 Executor、模型凭据或权限边界。
- 不以未安装的模型进行模型能力比较。

## Implementation steps

- [x] 核对现有 schema 与 benchmark 题目，定义可审计的 V2 契约。
- [x] 新增仅追加的 migration，并保持未知概念走开放式生成路径。
- [x] 将契约的显式查询形态约束合并到 Query Plan。
- [x] 补充 Resolver、Planner、SQL payload 聚焦测试。
- [x] 使用已配置评测账号运行 authenticated 小批评测，记录结果、模块文档、handoff、commit 与 push。

## Validation plan

- 运行 semantic resolver/query planner/model payload focused pytest。
- 运行 `npm.cmd run backend:test`。
- 运行认证评测抽样并与 `eval/reports/post_upgrade_full_eval.json` 对照；若回归则撤回运行链路变更。

## Risks

- `qwen2.5-coder:3b` 仍可能返回空 SQL 或错误 JSON；契约只能缩小语义歧义，不能替代模型能力。
- 契约约束过强可能误阻断开放式查询，因此只对已解析且版本化的契约应用。
