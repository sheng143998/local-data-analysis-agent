# 模块：综合 Agent 两百条测试用例

## 已完成行为

- 新增 `eval/datasets/comprehensive_agent_cases.jsonl`，共 200 条可审查测试用例。
- 新增 `eval/scripts/generate_comprehensive_agent_cases.py`，集中定义 case schema、七类配额、生成逻辑和完整性校验。
- 新增 focused tests，验证数量、唯一 ID、分类配额和路由/数据库/安全断言字段。

## 覆盖分布

| 类别 | 数量 | 核心断言 |
| --- | ---: | --- |
| 数据分析 | 75 | 进入 `data_analysis`，访问受控数据链路并生成 SQL |
| 普通聊天 | 40 | 进入 `general_chat`，不访问数据库、不生成 SQL |
| 结果解释 | 20 | 读取已保存结果，进入 `explain_result`，不访问数据库 |
| 澄清 | 20 | 请求业务范围，不访问数据库、不生成 SQL |
| 受限操作 | 15 | 进入 `unsupported`，拒绝越权或敏感请求 |
| 会话补充 | 15 | 合并待澄清上下文，保留会话所有权 |
| API 边界 | 10 | 验证鉴权、所有权、游标与参数错误边界 |
| 模型失败安全终止 | 5 | 覆盖超时、空 SQL、非 JSON、Guard/执行错误；返回安全失败且不得执行数据库 |

## 关键决策

- 用例集用独立 schema 表达跨路由断言，不修改仅面向 SQL 的 `run_eval.py` 契约。
- 本模块生成可执行测试资产，不执行 200 次云端模型调用；后续执行器必须按 `expected_route` 分流。
- 普通聊天、结果解释、澄清、拒绝和 API 边界都明确要求不访问数据库，防止路由退化为数据分析；5 条模型失败场景同样断言 503 不得执行数据库或泄露内部错误。

## 验证

- `python -m pytest backend/tests/test_comprehensive_agent_cases.py backend/tests/test_dialogue_router.py -q`：`11 passed`。
- `python eval/scripts/generate_comprehensive_agent_cases.py --output eval/datasets/comprehensive_agent_cases.jsonl`：生成 `200` 条，八类配额为 `75/40/20/20/15/15/10/5`。
- 尝试运行 `test_dialogue_router.py` 和 `test_conversation_service.py` 的组合回归在本机 120 秒窗口超时，未作为通过结果；新的 focused tests 已独立通过。
- `npm.cmd run frontend:build` 与 `git diff --check`：通过；仅有既有 bundle 大小提示。

## 风险与后续

- 当前用例集是质量契约和测试资产，尚未有统一跨路由执行器逐条运行 200 条。后续应实现 fixture 驱动执行器，不得把所有 case 发往 SQL 图。
- 云端模型可用性需要独立评测，不应与 schema 生成正确性混淆。
- 截图所示的 `503` 已映射为五条 `failure_safety` case：模型超时、空 SQL、非 JSON、Guard 拒绝和执行前错误都必须在数据库执行前安全终止。

## 交付

- 提交与推送结果待本模块 Git 操作完成后补充。
