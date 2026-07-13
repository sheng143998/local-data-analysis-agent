# 可恢复分批评测

## 完成行为

- `eval/scripts/run_eval.py` 支持 `--start`（0 起始偏移量）和 `--limit`，按 JSONL 中的稳定顺序选择连续 case；可连续执行 `0/10/20/...` 批次恢复 50 题基线。
- `--report` 支持为每一批指定独立报告路径，避免后续批次覆盖前一批报告。
- 报告新增 `dataset` 元数据：数据集路径、全量 case 数、选择起点/上限、本批 case 数、已运行 case ID 以及是否覆盖完整数据集。
- 非法偏移、非正 limit 和超出范围会在模型调用前明确阻断；评测鉴权和既有执行/严格成功率定义未变。

## 使用示例

```powershell
npm.cmd run eval:database-baseline -- --start 0 --limit 10 --report eval/reports/database_batch_001.json
npm.cmd run eval:database-baseline -- --start 10 --limit 10 --report eval/reports/database_batch_002.json
```

## 关键决定

- 分批报告只描述已运行 case，不自动合并或宣称为完整数据集结果，防止质量指标被误读。
- runner 仍要求鉴权开启时使用显式 `EVAL_AUTH_*` 账号登录，未关闭鉴权或创建临时用户。

## 验证

- `$env:PYTHONPATH='.'; .\.venv\Scripts\python.exe -m pytest backend/tests/test_eval_runner.py -q`：`17 passed, 1 warning`。
- `.\.venv\Scripts\python.exe eval/scripts/run_eval.py --help`：通过，显示 `--start`、`--limit`、`--report`。
- `npm.cmd run eval:database-baseline -- --start 0 --limit 10 --report eval/reports/database_batch_001.json`：真实管理员评测账号已登录；首批执行成功 `5/10`、严格成功 `2/10`、结果值匹配 `2/10`，平均 `26,234ms/case`。该报告只覆盖 `database_001` 至 `database_010`，不代表完整 50 题结果。
- 完整 `npm.cmd run eval:database-baseline` 已完成并更新 `eval/reports/latest_eval_report.json`：执行成功 `28/50`、严格成功 `11/50`、答案匹配 `10/48`、平均 `26,707ms/case`。该报告是后续语义层、Planner 与 Inspector 改造的起始基线。

## 风险与后续

- 单批运行仍可能受单题模型延迟影响；应按小批次运行并保留独立报告。
- 全量基线汇总需要读取每一批的 `dataset.selected_case_ids`，确认覆盖无重叠后再计算总指标。
- 本模块按并行协作约定不单独提交或推送，由主线在集成验证后统一提交。
