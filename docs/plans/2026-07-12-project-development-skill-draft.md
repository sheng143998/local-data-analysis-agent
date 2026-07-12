# 本地数据分析 Agent 开发 Skill 规范草案

> 状态：待审查。确认后将固化为项目内 `.agents/skills/` 的 Skill。

## 目标

建立可追溯的开发闭环：每次开发都从当前交接状态开始，以计划约束范围，以验证证明结果，并在完成后更新交接与模块记录。

## 强制工作流

### 1. 开发前

1. 读取 `docs/handoff/current.md`，确认当前状态、未完成事项、风险和最近验证结果。
2. 检查工作区状态和与任务相关的代码、测试、接口及已有文档；不得覆盖无关的未提交改动。
3. 在 `docs/plans/` 新建计划，命名为 `YYYY-MM-DD-<task-name>.md`。
4. 在开始代码改动前更新 `docs/handoff/current.md`：记录本次任务、影响范围、计划文档路径和已知风险。
5. 计划至少包含：`Goal`、`Scope`、`Out of scope`、`Implementation steps`、`Validation plan`、`Risks`。实施步骤以可更新的 checklist 表达。

### 2. 实施中

1. 遵守既有分层：API 保持薄层；业务编排进入 `services/`；Agent 流程进入 `agents/`；确定性能力进入 `tools/`；数据库访问通过 `db/repositories/`；契约放入 `schemas/` 与前端 `types/`。
2. 修改 API 契约时，同步检查后端路由和 schema、前端 API client 与 type、相关测试及 `docs/api*.md`，并遵循 `docs/api_change_process.md`。
3. 修改数据库结构时，新增迁移而非篡改已合入的历史迁移；同步 repository、schema、初始化/同步脚本与测试。
4. 修改 SQL 生成、检索、Guard、执行器或结果表达时，保持“模型不直接执行 SQL；SQL 必经意图校验、Guard 和只读执行”的边界；必要时运行标准评测。
5. 不提交真实密钥、数据库连接串或用户数据；普通用户界面不展示 prompt、工具 payload、向量评分或原始内部错误。
6. 中文文本文件默认使用 UTF-8 读取和写入；PowerShell 读取显式使用 `-Encoding utf8`。新建文本文件使用 UTF-8。除非文件已有明确编码，不用系统默认编码。

### 3. 完成前与完成后

1. 按计划运行与改动相称的验证；前端变更至少执行构建，后端变更执行相关测试，分析语义变更额外执行 `npm run eval:standard`。无法执行时必须记录原因。
2. 在 `docs/modules/` 新增完成记录，命名为 `YYYY-MM-DD-<task-name>.md`，包含：完成内容、关键决策、影响的接口/数据契约、验证命令与结果、已知风险或后续事项。
3. 更新 `docs/handoff/current.md`：完成状态、关键变更摘要、验证结果、遗留风险与下一步。Handoff 只保留当前状态和索引，不复制接口级实现细节。
4. 确认计划 checklist 与实际完成情况一致，再报告任务完成。

## 按影响范围的验证基线

| 改动类型 | 最低验证 |
| --- | --- |
| 前端页面、组件、类型或 API client | `npm.cmd run frontend:build` |
| 后端 Python 逻辑、路由、schema、repository | 相关 `pytest`；可用时 `npm.cmd run backend:test` |
| `/api/analyze`、检索、SQL Memory、SQL Generator、Guard、Executor、Presenter | 相关测试 + `npm.cmd run eval:standard` |
| API 契约 | 后端测试、前端构建、相关 smoke；同步 API 文档 |
| 数据库迁移或元数据同步 | 空库/目标库迁移验证、相关 repository 测试、必要的同步脚本小批量验证 |
| 仅文档 | 链接、路径、命令和描述与现状一致性检查 |

## 文档职责

- `docs/handoff/current.md`：当前项目状态、近期完成项、风险、下一步和重要文档索引。
- `docs/plans/`：任务开始前的实施计划与范围约束。
- `docs/modules/`：完成后的模块事实、验证结果和兼容性影响。
- `docs/api*.md`：对外/API 契约及前后端映射。
- `docs/testing/` 或对应计划/模块文档：失败复盘、验证细节和长期测试策略。

## 例外处理

- 纯答疑、只读分析、项目浏览和用户明确要求“不改文件”时，不新建计划或完成文档；但涉及当前状态时仍先读取 handoff。
- 紧急修复仍必须先创建最小计划并更新 handoff；计划可以简短，但不能后补替代“开发前”的记录。
- 用户明确要求跳过文档时，记录该例外及原因，不伪造完成文档或验证结果。

## 从上个项目吸收的原则

1. 把上下文文档视为开发会话入口，但将接口细节、验证和失败复盘下沉到专题文档，避免 handoff 膨胀和过期。
2. 用可观察、可评估的闭环替代“实现即完成”：关键 Agent/检索改动必须保留运行记录、回归用例和评估结果。
3. 明确数据写入责任和迁移归属，禁止通过临时 SQL 或 ORM 自动同步绕过迁移。
4. 让前端、API、AI 编排和数据库职责单一；跨边界变更必须同步契约和测试。
