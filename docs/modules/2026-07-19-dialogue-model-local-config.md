# 通用对话模型本地配置

## Completed behavior

- 本地 `backend/.env` 已增加完整 `DIALOGUE_MODEL_*` 配置占位项。
- 配置默认 `DIALOGUE_MODEL_ENABLED=false`，避免未填写 provider、endpoint、模型和 Key 时改变现有降级行为。
- `.env` 已验证为 Git 忽略文件，未提交任何本地模型信息或密钥。

## Validation

- `Settings` 非敏感读取：开关为 `False`、provider/model/base URL 为空、超时 `20s`、重试 `0`。
- `git check-ignore backend/.env`：确认受忽略规则保护。

## Next step

- 用户填写后将 `DIALOGUE_MODEL_ENABLED` 改为 `true`，重启后端并使用“什么是 RAG”等普通聊天验证真实模型回复。
