# 模块：语义意图规范化

## 完成行为

- `question_intent_parser` 已采用三层流程：模型先提取指标/维度候选，规范化层将候选映射为受控业务 ID，随后由既有 `QuerySpec` 约束必需表、指标 token、时间和 SQL 语义。
- Intent Prompt 新增 `metric_candidates` 与 `dimension_candidates`，允许模型保留“已支付订单”等自然语言业务概念；不再要求其只能输出预置 ID。
- 规范化层接受标准 ID、中文显示名和业务别名。它是下游安全契约的收敛层，不再作为用户问题是否被理解的唯一入口。
- 启发式仅在意图模型不可用或被显式关闭时作为兜底，并补充“订单总数”“总订单数”“订单总量”等订单计数表达。
- README 已记录云端 QLoRA/LoRA 微调模型通过 OpenAI-compatible `/v1/chat/completions` 接入本地 Agent 的配置边界。

## 关键决策

- 仍然只允许已定义的指标 ID 进入 QuerySpec。未知业务概念不能直接流入 SQL 生成，应由后续新增指标定义、QuerySpec 语义和测试后再支持。
- 云端模型只产生意图或 SQL 候选；无论模型部署在何处，最终 SQL 均继续经过 QuerySpec 校验、SQL Guard 和只读 Executor。
- 不在本模块执行云端训练或保存任何真实端点、密钥和模型配置。

## API 与数据契约影响

- 无新增 API、数据库迁移或前端字段。
- 意图模型响应兼容旧 `metrics`/`dimensions` 字段，新增可选 `metric_candidates`/`dimension_candidates` 字段；旧模型无需更新即可继续使用。

## 验证

- `.venv\\Scripts\\python.exe -m pytest backend/tests/test_question_intent_parser.py`：`9 passed`。
- `npm.cmd run backend:test`：`205 passed, 1 warning`。
- `npm.cmd run eval:standard`：268 秒完成，`13/20` 执行成功，`execution_success_rate=65.00%`，`strict_success_rate=60.00%`。本地模型输出具有波动性，单次提升不代表整体 SQL 质量已稳定达到生产标准。
- 人工检查 README 云端配置示例只包含占位地址和占位密钥。

## 剩余风险与后续

- 本地 `qwen2.5-coder:3b` 仍可能无法稳定生成复杂 SQL；应先积累人工确认的“问题、QuerySpec、正确 SQL、失败 SQL、修复 SQL”样本，再用云端 QLoRA 训练专用意图模型或 SQL 修复模型。
- 当前概念规范化仍包含有限业务别名。新指标应通过指标定义和 QuerySpec 扩展进入系统，不应仅靠增加字符串别名。
- 标准评测耗时接近五分钟，后续应单独优化评测模型、超时和诊断路径。

## 交付

- 模块提交：`2dc7154 优化语义意图规范化并支持云端模型`。
- 已推送至：`origin/main`。
