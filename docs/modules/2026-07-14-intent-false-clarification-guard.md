# 明确数据问题的错误澄清防护

## 完成行为

- 明确包含业务对象和查询操作的问题，在意图模型返回空候选错误澄清时保留原问题为自然语言业务候选，继续进入既有受控分析链路。
- 意图模型不可用而回退到启发式解析时，同一规则仍生效；维度识别不完整不会让用户重复补充已经给出的对象和操作。
- 模糊概览、问候和无业务对象的对话没有被该规则放行，仍由现有澄清或 Dialogue Router 处理。

## 安全和设计决策

- 规则必须同时命中查询操作和电商业务对象，且只影响空候选错误澄清；它不生成 SQL，也不绕过 Semantic Contract、Inspector、Guard 或只读 Executor。
- 原问题只作为自然语言候选进入下游检索，未新增固定 SQL、表名白名单执行逻辑或业务答案模板。

## 验证

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_dialogue_router.py backend/tests/test_conversation_service.py backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_clarification_policy.py -q`：`68 passed, 1 warning`。
- 全量认证真值集独立报告：`eval/reports/chat_upgrade_full_eval_20260714_v4.json`，执行 `25/50`、严格 `13/50`、答案 `14/48`；错误澄清降至 `0`，剩余 `25` 项失败均为空 SQL。
- `git diff --check`：通过。

## 质量结论和风险

- 严格成功和答案匹配恢复到可信基线 `13/50`、`14/48`，但执行成功仍低于 `post_upgrade_full_eval.json` 的 `31/50`，不能宣称数据质量不回退。
- 当前意图模型路由不可用，系统回退到启发式；本机只安装 `qwen2.5-coder:3b` 作为 SQL 模型，空 SQL 仍是主瓶颈。修复需要可用、稳定且获批准的意图/SQL 模型配置，不能用固定 SQL 绕过。

## 交付

- Commit：待生成并推送。
