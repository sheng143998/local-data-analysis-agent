# Evaluator Admin Account Validation

## Completed behavior

- 已确认 `eval/scripts/run_eval.py` 在 `AUTH_REQUIRED=true` 时要求 `EVAL_AUTH_EMAIL` 与 `EVAL_AUTH_PASSWORD`，通过 `/api/auth/login` 建立整批复用的测试会话。
- 已确认 `/api/analyze` 仅要求有效登录会话；关联的 `/api/runs` 与 `/api/runs/{id}` trace 读取要求 `admin` 角色。
- 本机数据库存在 3 个启用的管理员账号和 181 个启用的 analyst 账号；账号数量和状态已用只读查询核验，未读取或输出密码哈希。
- 已确认缺少评测环境变量会在执行 case 前以 `EvaluationConfigurationError` 明确阻断，不会写出伪造的质量报告。

## Key decisions

- 评测应使用已知密码的启用管理员账号，避免普通 analyst 账号造成 trace 静默缺失。
- 不从密码哈希恢复密码，也不修改既有管理员账号的密码或角色。
- 主线已创建本机专用管理员评测账号，并将随机凭据仅写入未跟踪 `backend/.env`；凭据不进入仓库、报告或文档。随后已成功运行首批真实数据库评测。

## API and data-contract impact

- 无 API、数据库结构或代码变更；本机仅新增了专用评测管理员数据。
- 无凭据、会话令牌、密码哈希或连接信息进入仓库。

## Validation

- 静态核对 `eval/scripts/run_eval.py`、`backend/app/api/auth.py`、`backend/app/api/dependencies.py`、`backend/app/api/runs.py` 与 `backend/app/services/auth_service.py`。
- 数据库只读聚合查询：管理员 `active=3`，analyst `active=181`。
- 隔离环境调用 `authenticate_evaluation_client(..., auth_required=True, environment={})`：收到预期的缺少 `EVAL_AUTH_*` 明确错误。

## Remaining risks and follow-up

- 完整 50 case 仍需按可恢复分批命令继续运行并汇总；首批 10 case 已成功执行。
- 按主线要求，本并行核验不单独提交；计划和模块记录由主线后续集成提交。
