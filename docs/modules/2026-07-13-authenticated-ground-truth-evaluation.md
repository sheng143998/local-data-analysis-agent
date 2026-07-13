# Authenticated Ground Truth Evaluation

## Completed behavior

- `eval/scripts/run_eval.py` 在开启鉴权时以 `EVAL_AUTH_EMAIL`、`EVAL_AUTH_PASSWORD` 登录评测账号；每个批次只创建并复用一个 TestClient 会话。
- 缺少凭据或账号登录失败会在运行 case 前明确阻断，不再把 401 写入报告并误判为模型或 SQL 质量下降。
- `EvalCase`、单 case 结果和汇总报告新增期望答案、实际行值序列化、答案匹配状态、答案不匹配原因，以及 `answer_match_rate`。
- 新增 `eval/datasets/database_ground_truth_questions.jsonl`，以 UTF-8 固化用户提供的 50 条真实数据库真值问题；包括数量、时间、支付、商品、退款、评价、履约和空结果场景。
- 新增 `npm.cmd run eval:database-baseline`；`backend/.env.example` 只提供评测账号变量占位符，不包含真实凭据。

## Key decisions

- 结果校验以 API 的结构化 `rows` 为来源，不解析自然语言 `summary`。
- 归一化只处理格式差异：空白、千分位、货币/单位、整数尾零和中英文分隔符；多行结果按期望片段逐项包含匹配，不依赖列别名或返回行顺序。
- “不可计算”场景保留真值文本但当前设为 `skip`，避免在缺少 Result Contract 前把展示策略差异误判为数据错误；空结果集单独使用 `empty` 模式校验。
- 不自动注册或创建评测用户，避免污染真实账号、会话和审计记录。

## API and data-contract impact

- 不改变对外 `/api/analyze`、鉴权 API、数据库 schema 或 SQL 执行边界。
- 评测 JSONL 可选字段：`expected_answer`、`expected_result_tokens`、`result_match_mode`；旧标准和回归数据集保持兼容。

## Validation

- `py -3 -m pytest backend/tests/test_eval_runner.py`：14 passed，1 warning。
- `npm.cmd run backend:test`：223 passed，1 warning。
- `npm.cmd run frontend:build`：通过。
- `npm.cmd run eval:database-baseline`：按预期阻断，提示本机缺少 `EVAL_AUTH_EMAIL` 和 `EVAL_AUTH_PASSWORD`；未将鉴权失败记为模型质量结果。

## Remaining risks and follow-up

- 配置具备管理员权限的专用评测账号后，执行 `npm.cmd run eval:database-baseline` 才能获得首份真实 50 case 质量基线和 run trace。
- 复杂多行和不可计算结果的严格语义校验应在后续 Result Contract 模块中升级为列名、类型和结构化值断言。
- 交付提交：`f0dd341 新增鉴权真实数据评测基线`，已推送至 `origin/main`。
