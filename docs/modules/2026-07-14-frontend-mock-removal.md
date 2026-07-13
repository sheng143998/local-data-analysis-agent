# 前端业务 Mock 清理

## 完成行为

- 删除 `frontend/src/data/mock.ts`，并清除 `frontend/src` 中所有对它的运行时引用。
- 查询历史页面读取管理员 `GET /api/runs` 的真实运行记录，支持本地搜索和查看真实 SQL、Guard、执行状态与错误信息。
- SQL Memory 页面读取管理员 `GET /api/memories` 的真实记录和可信状态；无数据、加载失败或无权限时不展示伪造模板。
- 评估概览仅从当前可访问的真实运行记录计算成功率、Guard 通过率、Memory 命中率、延迟和 ECharts 图表；它明确不是离线 benchmark 报告。
- 数据源页面因缺少安全公开元数据接口展示受限空态；遗留问答卡片、执行链路和结果表改为只接收调用方传入的真实数据。

## 关键决策

- 管理员接口保留其既有权限边界，未为了页面展示新建暴露 schema、SQL Memory 或内部评测数据的普通用户接口。
- API 失败、403 和空列表全部使用明确状态文本，而非回退到看似真实的演示内容。
- `PATCH` 加入通用 HTTP method 类型，保持后续 SQL Memory 审核操作的前端契约可用；本模块未新增该写操作。

## API 和数据契约影响

- 新增前端 `QueryRunRecord`、`SqlMemoryRecord` 类型及 `listRuns`、`listSqlMemories` client；不修改后端 API。
- `/api/runs` 与 `/api/memories` 仍要求管理员角色，普通账号应看到权限错误提示。

## 验证

- `npm.cmd run frontend:build`：通过。Vite 仅报告既有的大 chunk 提示，生产构建成功。
- `rg -n 'data/mock' frontend/src -g '*.ts' -g '*.tsx'`：无匹配。
- `git diff --check`：通过。

## 剩余风险和后续

- 查询历史、SQL Memory 与评估页面当前不在主导航路由中；需要暴露给管理员时应增加角色保护路由，而不是向普通用户开放数据。
- 高容量运行记录仍由现有 `/api/runs?limit=` 读取；需要分页时应新增后端 cursor 契约并同步前端。

## 交付

- Commit：待生成并推送。
