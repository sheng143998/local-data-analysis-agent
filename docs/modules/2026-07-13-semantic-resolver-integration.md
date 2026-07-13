# Semantic Resolver Integration

## Completed behavior

- `SemanticResolver` 按启用契约的 key、展示名和同义词绑定业务语义，未知明确概念不强制澄清。
- 唯一契约摘要进入 intent、检索上下文和 SQL 生成上下文；不生成 SQL，不绕过 QuerySpec、Guard 或只读 Executor。
- `009_semantic_contract_seed.sql` 初始化用户、订单和商品总数三个已验证快照契约。
- 相同 conflict group 的多个契约会写入结构化冲突；本阶段保留动态澄清文本，Phase 2 将由独立 Policy 接管。

## Validation

- Resolver、意图、会话和 Graph 聚焦测试：`57 passed, 1 warning`。
- 真实 PostgreSQL migration `009` 已应用。
- 后端全量：`234 passed, 1 warning`。

## Remaining risks

- 首批契约范围有限，未知指标继续依赖 schema 检索与模型生成。
- Clarification Policy 尚未独立，下一模块会以结构化 decision 接管当前冲突澄清。
