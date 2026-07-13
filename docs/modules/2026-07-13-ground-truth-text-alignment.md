# Ground Truth Text Alignment And Authenticated Evaluation

## Completed behavior

- 新增 `eval/scripts/compare_ground_truth_text.py`，使用 UTF-8（含 BOM 兼容）读取外部问答文本和项目 JSONL 真值集。
- 解析可选人工编号、章节标题和 `问题？答案` 行，比较 50 条问题顺序、问题文本和答案内容；仅对空白、中文/英文分隔符做格式归一化。
- 同时报告 JSONL 的 `expected_tables`/`expected_keywords` 元数据完整性；外部 txt 没有这些字段，不进行伪比较。
- 生成 `eval/reports/ground_truth_text_alignment.json`，同时引用已完成的全量升级报告并给出主失败类别；报告不包含密码、完整 prompt、SQL 或原始内部错误。
- 认证检查成功：`AUTH_REQUIRED=true` 时专用评测账号登录成功；密码只由项目配置加载，未输出、未写入报告。
- 认证第 1 批已运行并生成 `eval/reports/ground_truth_current_batch_001.json` 与对照摘要 `eval/reports/ground_truth_current_batch_001_alignment.json`。

## Alignment result

| Check | Result |
| --- | ---: |
| 外部 txt 条数 | 50 |
| JSONL 条数 | 50 |
| 问题文本差异 | 0 |
| 答案差异（归一化后） | 0 |
| 特殊结果场景 | 4（空结果 2、不可计算 2） |

因此，`C:\\Users\\admin\\Desktop\\新建 文本文档.txt` 与 `eval/datasets/database_ground_truth_questions.jsonl` 是同一套 50 case；外部文本中的自然语言“无数据/不可计算”分别由 JSONL 的 `empty`/`skip` 模式承载。

## Evaluation evidence

### Existing full upgrade report

来源：`eval/reports/post_upgrade_full_eval.json`，同一认证 50 case。

- 执行成功：31/50（62.00%）。
- 严格成功：13/50（26.00%）。
- 答案匹配：14/48（29.17%）。
- 主失败分类：应用/模型错误 18、缺少预期表 9、答案不匹配 7、SQL 语义断言缺失 2、空 SQL 1。

### Current authenticated batch 001

命令：

```text
npm.cmd run eval:database-baseline -- --start 0 --limit 10 --report eval/reports/ground_truth_current_batch_001.json
```

结果：执行成功 7/10（70.00%），严格成功 3/10（30.00%），答案匹配 3/10（30.00%），平均 32,071ms/case。

`database_001`（当前订单总数）返回 `99440`，真值为 `99441`；HTTP 200、Guard allowed、SQL 执行成功，但严格/答案断言失败。run trace 的生成路径为 `model_rewrite`，上下文含 `orders`、`payments`、`refunds`，SQL 表覆盖检查通过。该证据说明错误发生在模型改写/语义口径（多余支付 Join 或去重粒度）而不是认证或安全边界。

批次主失败分类：答案不匹配 2（`database_001`、`database_005`），应用/模型错误 3（`database_003`、`database_009`、`database_010`），缺少预期表 2（`database_004`、`database_006`）。

## Key decisions

- 外部 txt 只作为人工真值来源和对照输入，不进入运行时 Prompt、词表或固定 SQL。
- 评测报告按“主失败类别”对每个 case 只计一次，优先级为认证/HTTP、空 SQL、Guard、缺表、SQL 语义、危险关键字、答案不匹配、其他严格断言；这样可直接映射后续修复模块。
- 认证失败必须在 case 执行前阻断，不能把 401/403 当成模型质量；本次认证已通过。
- 当前 `database_001` 的错误不应通过固定订单数 SQL 绕过模型，应由 Query Plan/Inspector/语义契约和模型路由对照验证。

## API and data-contract impact

- 不修改公开 API、数据库 schema、Agent graph、Prompt、SQL Guard 或 Executor。
- 新增评测脚本参数仅用于本地数据集/报告路径；生成报告使用 UTF-8 JSON。
- 报告仅记录聚合质量、case ID、状态和安全摘要，不记录认证凭据、完整 SQL、prompt 或敏感样本值。

## Validation

- `.venv\\Scripts\\python.exe eval\\scripts\\compare_ground_truth_text.py --output eval\\reports\\ground_truth_text_alignment.json`：通过，`text=50`、`dataset=50`、问题差异 0、答案差异 0。
- `.venv\\Scripts\\python.exe eval\\scripts\\compare_ground_truth_text.py --eval-report eval\\reports\\ground_truth_current_batch_001.json --output eval\\reports\\ground_truth_current_batch_001_alignment.json`：通过，覆盖与批次结果一致。
- 认证登录 focused 检查：`auth_check=ok auth_required=True`。
- `npm.cmd run eval:database-baseline -- --start 0 --limit 10 ...`：完成，7/10 执行成功、3/10 严格成功；Starlette/httpx 兼容性 warning 不影响结果。
- `git diff --check`：待提交前执行。

## Remaining risks and follow-up

- 当前全量严格成功率仍只有 26%；下一步应按失败分类增加审核语义契约、Query Plan 对齐和模型路由 benchmark，不得增加固定 SQL 绕过链路。
- 第 1 批平均延迟约 32 秒/题；完整 50 case 需要分批运行，并以 case ID 集合核对无遗漏/重复。
- `database_001` 和 `database_005` 的错误聚合粒度需结合 SQL trace 和 Inspector 规则继续定位；本模块不改核心 graph。

## Delivery

- 本模块文件：本计划、对照脚本、对照报告、认证批次报告及本记录。
- Commit/push：`ef14aa0`（`完善数据库真值文本对照评测`）、`5a65b26`（补录交付记录）、`d8ba195`（补充 JSONL 元数据完整性校验），均已推送至 `origin/main`。共享 handoff 的完成状态已更新到工作树，但因同时包含其他 agent 未提交改动，未在本模块提交中暂存。
