# 订单支付状态语义契约覆盖

## 目标

根据 authenticated 50-case 基线中订单状态、支付状态、支付方式记录数和支付方式已支付金额的失败分类，补齐可审计的语义契约，使 Resolver、Query Plan、Context Pack 与 SQL 模型共享同一业务粒度和过滤口径。

## 范围

- 新增订单状态分布、支付状态分布、支付方式记录数、支付方式已支付金额四个版本化契约。
- 契约只声明来源表字段、默认支付状态过滤和结果形态，不保存或执行 SQL。
- 为 Resolver 绑定和 Query Planner 继承计划形态增加数据库无关 focused tests。

## 非范围

- 不为单个评测问题写固定 SQL，不绕过模型、Inspector、Guard 或只读 Executor。
- 不修改公开 API、鉴权、模型凭据和并发处理。
- 不把未知业务概念强制收敛到本批契约。

## 实施步骤

- [x] 核对 50-case 真值、数据库列和现有契约，确定四个稳定口径。
- [x] 新增仅追加的 `013` 语义契约 seed migration。
- [x] 增加 Resolver/Planner 回归测试，验证状态维度、支付方式维度、`paid` 默认过滤和结果形态。
- [x] 运行 focused tests，补模块完成记录并更新 handoff。
- [ ] 只提交本模块文件并推送，保留其他未提交评测工件不变。

## 验证

- `py -3 -m pytest backend/tests/test_semantic_resolver.py backend/tests/test_query_planner.py backend/tests/test_semantic_contracts.py`
- `git diff --check`
- 若本机数据库可用，再确认 migration 可重复执行且 `ON CONFLICT` 不覆盖既有版本；不把未运行的完整 benchmark 宣称为通过。

## 风险

- 本地 3B SQL 模型仍可能返回空 SQL 或错误 Join；契约只缩小语义歧义，不能替代模型能力。
- `payments` 一单多支付时金额契约必须明确按支付记录金额汇总，订单金额不能直接与支付记录 Join 后重复累计。
