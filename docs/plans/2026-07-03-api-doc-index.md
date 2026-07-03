# 接口文档索引与阅读顺序计划

当前正在做：接口文档索引与阅读顺序已补齐且验证通过，准备提交并推送。

## Goal

当前接口文档已经拆分为多个主题文档，需要一个中文索引说明每份文档的用途、适合谁阅读、何时更新，避免 README 入口越来越长但缺少阅读路径。

## Scope

- 包含：
  - 新增 `docs/api_index.md`。
  - 更新 README 和各接口文档入口。
  - 更新 handoff 和模块完成说明。
- 不包含：
  - 修改 API 实现。
  - 修改前端 API client。
  - 修改测试代码。
  - 新增接口。

## Module Boundary

- 上游输入：
  - `README.md`
  - `docs/api.md`
  - `docs/api_frontend_mapping.md`
  - `docs/api_error_auth.md`
  - `docs/api_change_process.md`
  - `docs/api_smoke_examples.md`
- 输出：
  - 中文接口文档索引与阅读顺序说明。

## Business Logic

- 新加入项目的人先读索引，再按角色进入对应接口文档。
- 前端联调、后端接口修改、测试验证、上线前审查各有不同阅读路径。
- 文档索引应明确这些文档都是当前 V1 接口契约说明，不代表新增功能。

## Data Contract

本模块不改变任何接口契约，只组织现有接口文档。

## Implementation Steps

任务清单：
- [x] 创建计划文档。
- [x] 梳理现有接口文档体系。
- [x] 新增接口文档索引。
- [x] 更新 README、相关接口文档、handoff 和模块完成说明。
- [x] 运行验证命令。
- [x] 提交并推送。

## Validation Plan

- `npm run backend:test`
- `npm run frontend:build`
- `npm run test:e2e`

## Risks and Open Questions

- 索引文档需要随着接口文档拆分继续维护。
- 如果后续生成 OpenAPI 页面，需要在索引中补充自动文档入口。
