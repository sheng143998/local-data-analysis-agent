# Authenticated Ground Truth Evaluation

## Goal

落实复合式数据分析 Agent 升级草案的 Phase 0：在 `AUTH_REQUIRED=true` 时让评测使用显式评测账号完成登录，并将用户提供的 50 条真实数据库问题固化为版本化基准集，支持 SQL 断言之外的结果值校验。

## Scope

- 为 `eval/scripts/run_eval.py` 增加受控鉴权登录流程；鉴权启用时从环境变量读取评测账号，不创建、注册或修改用户。
- 保持未启用鉴权时现有开发主体行为不变。
- 将 `C:\\Users\\admin\\Desktop\\新建 文本文档.txt` 的 50 条问题和答案转换为仓库内 UTF-8 JSONL 数据集。
- 扩展评测数据契约、结果和报告，记录期望答案、实际结果、结果匹配状态及不匹配原因。
- 增加数据集加载、答案归一化和鉴权失败提示的聚焦测试，并提供独立 npm 脚本。

## Out of scope

- 不改变 SQL Guard、只读 Executor、业务 SQL 生成、模型路由或用户登录 API。
- 不自动创建评测账号，不在代码、报告或文档中写入账号密码。
- 不承诺本阶段修复 50 条问题的 SQL 生成质量；本模块只建立可复现的真实质量基线。
- 不实现并发评测、评测结果数据库持久化或跨模型对比面板。

## Implementation steps

- [x] 定义评测账号环境变量和 TestClient 登录逻辑，鉴权失败时给出明确阻断信息。
- [x] 扩展评测用例和报告，支持 API 返回结果的规范化值比较。
- [x] 固化 50 条数据库真值问题集，并为其补充最小 SQL 结构断言。
- [x] 新增 npm 运行入口和聚焦自动化测试。
- [x] 运行聚焦测试、后端全量测试、前端构建和鉴权评测前置条件验证。
- [x] 记录模块交付、更新 handoff、提交并推送。

## Validation plan

- `py -3 -m pytest backend/tests/test_eval_runner.py`
- `npm.cmd run backend:test`
- `npm.cmd run frontend:build`
- 使用 `EVAL_AUTH_EMAIL` 和 `EVAL_AUTH_PASSWORD` 配置后运行 `npm.cmd run eval:database-baseline`；若本机未配置评测凭据，验证其明确失败信息，不将 `401` 伪装为模型质量结果。

## Validation result

- `py -3 -m pytest backend/tests/test_eval_runner.py`：14 passed，1 warning。
- `npm.cmd run backend:test`：223 passed，1 warning。
- `npm.cmd run frontend:build`：通过。
- `npm.cmd run eval:database-baseline`：按设计以非零状态明确阻断，原因是本机 `AUTH_REQUIRED=true` 但未配置 `EVAL_AUTH_EMAIL` 和 `EVAL_AUTH_PASSWORD`；未生成伪造的 401 质量报告。

## Risks

- 真实模型可能导致完整 50 case 评测耗时较长或不稳定；报告必须将鉴权、执行、SQL 断言和结果值断言分开。
- 现有 `/api/runs` 仅管理员可读取；非管理员评测账号可执行评测，但不会带运行轨迹摘要。
- API 的通用展示结果可能包含格式差异；答案比较只做安全、可解释的空白、标点、千分位、百分比和行序归一化，复杂业务口径仍需通过结果真值确认。
