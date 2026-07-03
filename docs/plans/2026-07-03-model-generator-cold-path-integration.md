# Model SQL Generator cold_path 接入计划

当前正在做：Model SQL Generator cold_path 配置开关接入已完成实现、测试和文档更新，等待提交并推送。

## Goal

让 `/api/analyze` 具备可选的模型 SQL 生成路径，为后续摆脱固定 SQL 模板打基础。默认不开启模型生成，避免本地未配置模型服务时影响当前可用闭环。

## Scope

- 包含：
  - 新增 `MODEL_SQL_GENERATOR_ENABLED` 配置。
  - `cold_path` 开启配置时尝试调用 model-backed SQL Generator。
  - 模型失败或未返回 SQL 时退回现有确定性生成。
  - 模型生成 SQL 继续进入 SQL Guard 和只读 Executor。
  - 增加聚焦测试。
  - 更新 README、模块说明和 handoff。
- 不包含：
  - 默认启用真实模型生成。
  - 完整替换现有模板链路。
  - 流式输出模型过程。
  - 前端展示模型状态或 prompt。

## Module Boundary

- 上游输入：`run_analysis_graph(question)` 中已构建的 `RetrievalContext` 和 `SqlReusePlan`。
- 核心处理：根据开关和 path 选择模型生成或现有确定性生成。
- 下游输出：`GeneratedSql`，随后进入现有 `guard_sql()`、`execute_guarded_sql()`、presenter 和 logger。

## Business Logic

- 普通用户继续看到同一个数据问答结果结构。
- 未配置模型服务时默认不调用模型。
- 开启模型后，只有 `cold_path` 尝试模型生成；`fast_path` 和 `rewrite_path` 继续优先复用历史成功 SQL 或确定性改写。
- 模型生成失败不会直接报给普通用户，而是退回稳定生成路径并记录 warning。

## Data Contract

- 环境变量：`MODEL_SQL_GENERATOR_ENABLED=false|true`
- Graph 内部：`GeneratedSql.path` 可为 `model_generate`、`model_error` 或原有路径。
- 日志：`tool_calls.output_payload.generation_path` 会记录最终采用的生成路径。

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 实现配置开关和 graph 选择逻辑。
- [x] 添加聚焦测试。
- [x] 更新 README、模块完成文档和 handoff。
- [~] 运行验证并提交推送。

## Validation Plan

- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and Open Questions

- 模型 SQL 质量仍需评估集验证。
- 当前默认关闭模型生成，后续需要在本地模型服务稳定后再打开并跑标准问题集。
