# 统一 ModelAdapter 基础层计划

当前正在做：统一 ModelAdapter 基础层已完成实现、测试和文档更新，等待提交并推送。

## Goal

V1 后续不能继续依赖新增固定 SQL 模板，需要统一模型调用入口。该模块先提供可配置、可测试、可追踪的 ModelAdapter 基础能力，让后续 SQL Generator 通过统一 adapter 调用模型，而不是在节点里直接调用 SDK 或 HTTP。

## Scope

- 包含：
  - 扩展后端配置，读取模型 provider、base URL、model、timeout、retry 等设置。
  - 新增 `ModelAdapter`，支持 OpenAI-compatible chat completions 请求结构。
  - 定义结构化请求、响应、错误和元数据。
  - 增加无真实密钥的单元测试。
  - 更新 README、模块说明和 handoff。
- 不包含：
  - 在 `/api/analyze` 中启用真实模型生成 SQL。
  - 写入真实 API key。
  - 前端展示模型状态。
  - embedding adapter。

## Module Boundary

- 上游输入：后续 SQL Generator / Rewriter 传入的 messages、temperature、max tokens。
- 核心处理：统一配置、HTTP transport、timeout、retry、结构化错误。
- 下游输出：`ModelResponse`，包含文本、provider、model、latency、token 和 cost 元数据占位。

## Business Logic

- 普通用户不感知模型提供商和连接状态。
- 开发者通过配置选择本地或 OpenAI-compatible endpoint。
- 所有外部模型调用必须经过该 adapter，便于后续统一日志、超时、重试和成本统计。

## Data Contract

- `ModelMessage`
- `ModelRequest`
- `ModelResponse`
- `ModelUsage`
- `ModelError`

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 实现配置、adapter 和结构化模型契约。
- [x] 添加单元测试。
- [x] 更新 README、模块完成文档和 handoff。
- [~] 运行验证并提交推送。

## Validation Plan

- `npm run backend:test`
- `npm run test:e2e`
- `npm run frontend:build`

## Risks and Open Questions

- 本模块只提供基础调用入口，不代表 `/api/analyze` 已经由模型生成 SQL。
- 真实 provider 的鉴权、流式输出和工具调用会在后续模块逐步接入。
