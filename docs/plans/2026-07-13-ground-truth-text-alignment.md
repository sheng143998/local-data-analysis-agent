# Ground Truth Text Alignment And Authenticated Evaluation

## Goal

核验用户提供的 `C:\\Users\\admin\\Desktop\\新建 文本文档.txt` 与项目数据库真值集的一致性，并基于同一 50 case 数据集分类当前认证评测失败，为后续语义契约、SQL 模型路由和 Inspector 改造提供可重复证据。

## Scope

- 以 UTF-8 读取外部 txt 和 `eval/datasets/database_ground_truth_questions.jsonl`。
- 比较 case 数量、顺序、问题文本、期望答案、表/关键字和空结果/不可计算模式。
- 使用现有 `EVAL_AUTH_*` 配置执行或准备可恢复的认证分批评测；不记录或提交凭据。
- 从现有报告提取失败阶段并生成独立对照报告与模块记录。

## Out of scope

- 不修改核心 Agent graph、模型 Prompt、SQL Guard、Executor、数据库迁移或公开 API。
- 不新增固定 SQL，不绕过认证、Inspector、Guard 或只读执行链路。
- 不把外部 txt 的答案写入运行时配置。

## Implementation steps

- [x] 检查现有评测数据集、runner、认证配置和基线报告。
- [x] 实现/运行 txt 与 JSONL 对照，输出可审计差异报告。
- [x] 执行认证第 1 批并分类已有全量/当前批次失败；完整 50 case 保留为可恢复分批任务。
- [x] 编写完成模块记录，更新 handoff，记录验证与后续建议。
- [ ] focused 验证通过后仅提交本子任务文件并推送。

## Validation plan

- `py -3 eval/scripts/compare_ground_truth_text.py`（或等价 focused 对照命令）。
- 对照报告必须显示 50/50 覆盖、问题与答案差异数、特殊模式差异数。
- 如运行认证评测，使用 `npm.cmd run eval:database-baseline -- --start ... --limit ... --report ...`，核对 case ID 覆盖和报告中的认证状态。
- `git diff --check`，并验证 JSON/Markdown 可 UTF-8 读取。

## Risks

- 外部 txt 可能包含人工编号、中文标点或答案格式差异，解析需保留原始文本并只归一化可解释格式。
- 认证评测耗时较长或本地模型不稳定，单批报告不能替代完整覆盖结论。
- 当前工作树已有其他 agent 的评测工件，提交时必须只选择本子任务文件。
