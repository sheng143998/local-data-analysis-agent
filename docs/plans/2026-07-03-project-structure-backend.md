# 本地数据分析 Agent 项目结构与后端开发计划

Goal: 将当前单层前端工程整理为前后端清晰分层的本地数据分析 Agent 项目，并建立 FastAPI 后端最小闭环。

当前正在做：模块已完成，前端构建和后端 smoke/API 测试均已通过。

Scope:
- 包含：前端目录迁移、根目录脚本整理、FastAPI 后端骨架、最小 `/api/analyze` 与 `/api/health`、后端 schema/service/tool/agent 边界、 smoke 测试与文档更新。
- 不包含：真实 PostgreSQL 连接、真实 LangGraph 编排、真实 LLM 调用、真实 pgvector 检索、生产部署配置。

Module boundary:
- Upstream inputs: 前端自然语言问题、指标口径配置、环境变量。
- Downstream outputs: 分析摘要、SQL、结果表、来源信息、trace 元数据。
- Likely touched files: `frontend/`, `backend/`, `docs/`, root `package.json`, tests/smoke scripts.

Business logic:
- 用户在前端聊天式问答页输入业务问题。
- 前端通过集中 API client 调用后端。
- 后端返回可追溯分析结果：自然语言结论、SQL、结果表、来源与安全状态。
- 系统技术细节保留在后端 trace，不默认暴露给普通用户。

Data contract:
- `POST /api/analyze`
  - Request: `{ "question": string }`
  - Response: `{ question, path, summary, sql, metrics, rows, source, trace, steps }`
- `GET /api/health`
  - Response: `{ ok, service, version }`

Implementation steps:
- [x] 创建计划文档
- [x] 将 React + Vite 前端移动到 `frontend/`
- [x] 创建根目录脚本与项目说明
- [x] 创建 `backend/` FastAPI 分层目录
- [x] 实现后端最小分析服务与 API
- [x] 增加后端 smoke 测试
- [x] 更新前端 API 调用集中到 `frontend/src/api/`
- [x] 运行前端构建与后端 smoke 测试

Validation plan:
- `cd frontend && npm run build`
- `cd backend && python -m pytest` 或可用的 smoke check
- 调用 `/api/health` 与 `/api/analyze` 验证最小闭环

Risks and open questions:
- 当前后端先使用 mock Agent 服务，不连接真实数据库。
- 如果本地未安装 FastAPI/pytest，需要先安装后端依赖。
- 旧 Node `node_modules` 可能仍留在根目录，作为本轮迁移后的可清理项。
