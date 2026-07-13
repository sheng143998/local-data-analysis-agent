# 可恢复分批评测计划

## Goal

使长耗时真实库评测可以按稳定顺序分段运行，并在报告中明确记录原始数据集、选择范围和已运行 case，避免单次 50 题超时后没有可追溯结果。

## Scope

- 为 `eval/scripts/run_eval.py` 增加基于 0 起始偏移量的 `--start` 和 `--limit` 参数。
- 对非法分段参数和超出数据集范围提供明确阻断错误。
- 在报告保留既有质量指标定义，并新增数据集与本批执行范围元数据。
- 补充分段选择、报告元数据和参数校验的聚焦测试。

## Out of scope

- 不改变 SQL、Guard、结果值、鉴权和 strict 成功率的判定规则。
- 不合并不同批次报告，也不创建或绕过评测账号。
- 不改动 Agent、模型、数据库或前端。

## Implementation steps

- [x] 增加可验证的 case 分段选择函数。
- [x] 在 CLI 接入 `--start` / `--limit` 并把批次元数据写入报告。
- [x] 补充单元测试。
- [x] 运行聚焦测试并核对 CLI 帮助。
- [x] 完成模块记录与 handoff 状态。

## Validation plan

- `pytest backend/tests/test_eval_runner.py -q`
- `python eval/scripts/run_eval.py --help`
- 使用纯函数测试确认每个分段不重叠且超出范围被阻断。

## Risks

- 分段报告只表示本批，不代表完整 50 题基线；报告元数据必须防止误读。
- 实际模型耗时仍由模型服务决定，分段只能保证单批可控和可恢复。
