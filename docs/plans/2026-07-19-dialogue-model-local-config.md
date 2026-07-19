# 通用对话模型本地配置

## Goal

在本地 `backend/.env` 增加独立通用对话模型配置项，允许用户自行填写已批准的云端模型信息，不自动复用 SQL 或 Intent 密钥。

## Scope

- 仅修改被 Git 忽略的本地 `backend/.env`。
- 添加 `DIALOGUE_MODEL_*` 配置占位项，默认关闭。

## Out of scope

- 不写入、复制、提交或展示任何 API Key。
- 不修改应用代码、模型路由或数据库。

## Implementation steps

- [x] 确认当前 Dialogue 配置未启用。
- [x] 写入本地配置占位项。
- [x] 验证配置文件可由 Settings 读取，记录完成状态。

## Validation plan

- 使用 `Settings` 读取非敏感字段，确认开关、provider、base URL 与模型名被加载。

## Risks

- 配置不完整时 DialogueService 会安全回退为本地固定回复，不会影响 SQL 安全链路。
