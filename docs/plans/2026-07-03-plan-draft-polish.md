# 可执行计划草案完善计划

Goal: 将 `executable-plan-draft.md` 完善为当前项目可直接执行的 V1 研发方案，消除旧决策和当前实现之间的不一致。

当前正在做：草案已完善完成，已检查旧路线残留关键词。

Scope:
- 包含：V1 定位、项目结构、模块边界、后端开发顺序、数据库/指标/SQL 记忆设计、API 契约、前端产品形态、测试验收、里程碑。
- 不包含：真实代码实现、真实数据库迁移、真实模型适配。

Module boundary:
- Upstream inputs: 现有草案、当前项目目录、已实现前端/后端最小闭环。
- Downstream outputs: 完善后的 `executable-plan-draft.md`。
- Likely touched files: `docs/plans/2026-07-03-plan-draft-polish.md`, `executable-plan-draft.md`。

Business logic:
- 草案需要指导后续开发，不只是概念说明。
- 普通用户前端以聊天式分析和指标 CRUD 为主，不暴露模型/数据库状态。
- 后端按 FastAPI + services/agents/tools/db/schemas 分层推进。

Data contract:
- 文档中明确 `POST /api/analyze`、指标 CRUD API、数据源 API、runs/memories 调试 API。
- 明确 LangGraph state、SQL Memory、Query Runs、Tool Calls、Metric Definitions 等核心字段。

Implementation steps:
- [x] 读取 skill 与现有草案
- [x] 重写可执行计划草案
- [x] 检查文档与当前项目结构一致性
- [x] 完成模块说明与验证记录

Validation plan:
- 读取完善后的文档，检查是否仍包含 SQLite/Streamlit 作为 V1 主线等旧决策。
- 检查是否覆盖当前已实现目录和后续后端开发模块。

Risks and open questions:
- 草案仍是研发路线文档，不代表全部模块已实现。
- 后续真实数据库和模型选型仍需在开发过程中进一步确认。
