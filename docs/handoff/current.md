# 当前 Handoff

## 当前状态

- 项目已连接 GitHub：`https://github.com/sheng143998/local-data-analysis-agent`
- 当前分支：`main`
- 前后端目录已拆分：
  - `frontend/`: React + Vite + TypeScript 前端
  - `backend/`: FastAPI 后端
  - `docs/`: 草案、计划、handoff
- 当前普通用户产品方向：聊天式数据问答 + 指标口径 CRUD，不默认展示模型、数据库连接状态、SQL 记忆细节和评估报告。

## 最近完成模块

### 1. 项目结构与 FastAPI 最小闭环

- commit: `8071783 初始化项目结构并通过前后端验证`
- 内容：
  - 创建 `frontend/` 和 `backend/`
  - FastAPI mock `/api/analyze`
  - 前端聊天式问答页
  - 根目录项目脚本
- 验证：
  - `npm run frontend:build`
  - `npm run backend:test`
  - `npm run test:e2e`

### 2. 指标口径后端 CRUD

- commit: `094ecf2 实现指标口径后端CRUD并通过测试`
- 内容：
  - `GET/POST/PUT/DELETE /api/metrics`
  - `MetricService`
  - 内存版 `MetricRepository`
  - `metric_definitions` migration
  - 前端指标页接入 `metricClient`
- 验证：
  - `npm run backend:test`，3 个测试通过
  - `npm run frontend:build`
  - `npm run test:e2e`

## 当前架构边界

- React 只通过 `frontend/src/api/` 调 FastAPI。
- FastAPI API 层保持薄层。
- 业务逻辑放在 `services/`。
- Agent 编排放在 `agents/`。
- 确定性工具放在 `tools/`。
- 数据库访问后续放在 `db/repositories/`。
- 数据库结构必须放在 `backend/app/db/migrations/`。

## 当前正在做

建立 handoff 工作流：每次任务开始必须读取 `docs/handoff/current.md`，每次模块完成或阻塞必须更新该文件。

## 下一步建议

按 `executable-plan-draft.md` 继续 M1/M2：

1. 建立 PostgreSQL 连接配置和 repository 基类。
2. 将指标 CRUD 从内存 repository 替换为 PostgreSQL repository。
3. 增加 migration runner 或初始化脚本。
4. 为 metric repository 增加集成/烟雾测试。

## 已知风险

- 当前指标 CRUD 使用内存仓储，重启后数据丢失。
- `metric_definitions` migration 已写，但尚未接入真实数据库执行流程。
- SQL Guard、SQL Validator、只读 Executor 尚未实现。
- `FastAPI TestClient` 当前有 `StarletteDeprecationWarning`，不影响功能，但后续可评估依赖版本。

## 每次继续开发前必须做

1. 读取本文件。
2. 读取相关 `docs/plans/*.md`。
3. 确认当前 git 状态。
4. 开发模块前创建或更新计划文档。
5. 模块完成后运行相关验证。
6. 更新本文件。
7. commit 并 push。
