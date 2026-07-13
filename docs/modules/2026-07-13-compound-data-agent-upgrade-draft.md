# 复合式数据分析 Agent 升级草案交付记录

## Completed

- 新增 `docs/plans/2026-07-13-compound-data-agent-upgrade-draft.md`。
- 综合 Snowflake Cortex Analyst、Databricks Genie、LangChain SQL Agent、Wren AI 和 Vanna 的公开机制，形成适配当前 FastAPI、LangGraph、PostgreSQL、Redis 和 React 架构的升级方案。
- 草案覆盖 Semantic Layer V2、Clarification Policy、Trusted SQL、Query Plan、Context Pack、SQL Inspector、`EXPLAIN`、分类 Repair、Result Contract、评测、治理和模型路由。
- 明确本次只交付待审查文档，不修改业务代码、数据库、API、配置和前端。

## Key Decisions

- 推荐先实施 Phase 0：修复 authenticated eval runner 并建立基线。
- 不继续通过单问题 Prompt 特例或固定 SQL 扩展主链路。
- 保留开放式语义候选；语义层提供业务契约，不作为封闭词表。
- 只有 verified SQL 可进入高置信 fast path，执行成功 SQL 只能成为待审核候选。
- SQL Generator、Inspector、Guard 和 Executor 保持职责分离。

## API And Data Impact

- 无 API、数据库和运行时影响。
- 草案中的数据结构均为候选设计，实施前必须另建计划和 migration 评审。

## Validation

- 使用 UTF-8 读取并对照 `docs/architecture.md`、`docs/agent_workflow.md`、`docs/evaluation.md`、现有会话记忆草案和当前 handoff。
- 核对草案未放宽 QuerySpec、SQL Guard、只读 Executor、鉴权和会话所有权边界。
- 核对每个 Phase 均具备目标、范围和可独立验收条件。

## Remaining Work

- 等待用户审查并回答草案末尾的 Review Questions。
- 审查通过后只为 Phase 0 创建实施计划，不直接开始后续 migration 或模型替换。

