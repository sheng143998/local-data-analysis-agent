# 前端业务 Mock 清理

## Goal

移除遗留管理、历史、SQL Memory、评估和数据问答组件中的前端业务 Mock，使页面仅展示后端真实数据，或在尚未提供安全公开接口时展示清晰的空态。

## Scope

- 将查询历史和 SQL Memory 页面接入已有的管理员只读 API。
- 使用真实运行记录构建评估概览，不制造成功率、失败案例或图表数据。
- 将遗留数据问答展示组件改为由调用方传入真实响应数据。
- 删除 `frontend/src/data/mock.ts` 和所有运行时引用。
- 数据源元数据暂不新增接口，保留不含模拟数据的受限空态。

## Out of scope

- 不新建会暴露 schema、原始数据或内部评测详情的普通用户 API。
- 不改变 SQL Agent、权限模型、评测执行或数据库结构。
- 不以硬编码默认值伪装真实的运行、记忆或评估数据。

## Implementation steps

- [x] 定义管理员运行记录和 SQL Memory 的前端契约及 API client。
- [x] 用真实 API 重写查询历史、SQL Memory 和评估页面。
- [x] 将遗留数据问答组件改为受控展示组件，删除 Mock 数据模块。
- [x] 执行前端构建、Mock 引用扫描和 diff 检查。
- [x] 记录模块、更新 handoff、独立提交并推送。

## Validation plan

- `npm.cmd run frontend:build`。
- `rg -n 'data/mock' frontend/src -g '*.ts' -g '*.tsx'` 无运行时引用。
- `git diff --check`。
- 检查加载、空数据和管理员接口不可用时不展示虚假业务数据。

## Risks

- `/api/runs` 和 `/api/memories` 限制管理员访问；非管理员会收到权限提示而非展示模拟数据。
- 运行记录不是离线评测报告，评估页只能呈现实时可访问运行摘要，不能将其称为正式 benchmark。
