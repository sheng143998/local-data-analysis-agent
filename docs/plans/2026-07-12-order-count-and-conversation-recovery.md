# 订单计数与会话恢复修复计划

## Goal

修复“当前订单总数是多少”仍返回 503，以及登录后无法恢复会话历史的问题。对语义明确、单指标的已支付订单数提供受控 SQL fallback；为会话增加 PostgreSQL 持久化副本，避免 Redis 不可用或后端重启时历史丢失。

## Scope

- 为无维度的单一 `order_count` QuerySpec 构造确定性、已支付口径的 SQL fallback，并继续经过 SQL 意图校验、Guard 和只读 Executor。
- 失败的分析也保存用户提问与安全错误摘要，使其可在会话历史中恢复。
- 新增会话状态 PostgreSQL 持久化表与仓储；Redis 可用时仍保留其作为快速会话层，数据库副本用于恢复与列表读取。
- 在前端分析失败后刷新会话列表，并在会话恢复时显示已保存的失败摘要。
- 明确开发环境必须启用 `AUTH_REQUIRED=true` 才能按真实账号隔离和恢复会话；提供仅管理员可显式执行的本机匿名历史迁移，不在普通登录时自动转移。
- 同步 API 文档、测试、模块记录与 handoff。

## Out of scope

- 不恢复已经仅存在于已退出进程内存中的历史会话。
- 不在普通登录流程自动认领匿名开发会话；迁移只能由管理员显式触发。
- 不放宽 SQL Guard、支付订单口径、只读 Executor 或跨用户会话隔离。
- 不实现 Redis 高可用、异步归档、多设备合并、并发控制或会话全文检索。

## Implementation steps

- [x] 增加会话状态迁移、PostgreSQL 仓储与 Redis/数据库组合存储。
- [x] 将失败分析持久化为会话中的安全错误摘要。
- [x] 增加受控 `order_count` fallback，并保证继续经过意图校验、Guard 和 Executor。
- [x] 更新前端失败后的会话刷新与历史错误展示。
- [x] 设置本机鉴权配置为启用，并记录无法恢复的匿名内存会话边界。
- [x] 补充后端、API 和前端测试，执行 migration、focused pytest、后端全量和前端构建；标准评测报告完成但进程在 364 秒超时，已据实记录。
- [x] 创建完成记录、更新 handoff、提交并推送。

## Validation plan

- 执行新 migration 并检查会话状态表。
- focused conversation、analysis graph、API tests。
- `npm.cmd run backend:test`。
- `npm.cmd run frontend:build`。
- `npm.cmd run eval:standard`。
- 手工 smoke：登录后提交失败分析，刷新页面后仍能在会话列表恢复；订单总数返回成功查询。

## Risks

- Redis 停止期间，新 PostgreSQL 副本可保证会话可恢复，但不会找回已在旧进程内存中消失的记录。
- 受控 fallback 只覆盖单一订单数，不应扩展为绕过模型和业务语义校验的通用模板系统。
- 本机启用鉴权后，浏览器必须重新登录；以前的匿名开发会话不能自动安全归属。
