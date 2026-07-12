# 语义意图规范化计划

## Goal

将当前以关键词词表为主的意图识别，调整为“模型候选抽取、业务概念规范化、QuerySpec 与检索上下文校验”三层架构。保留标准指标 ID 和 SQL 安全边界，但不再要求用户措辞必须命中固定词表。

## Scope

- 扩展意图模型输出，允许其给出自然语言指标和维度候选。
- 新增业务概念规范化层，将模型候选、标准 ID、中文指标名与少量同义表达映射为受控 ID。
- 将本地启发式从唯一理解路径降级为模型不可用时的兜底，并补足常见订单总数表达。
- 通过 QuerySpec 保持下游 SQL 生成、校验和 Guard 的受控契约。
- 补充云端 OpenAI-compatible 微调模型的配置与接入说明。
- 增加解析器 focused tests，并执行后端全量测试与标准评测。

## Out of scope

- 不执行云端训练，不写入任何真实云端密钥。
- 不放宽 SQL Guard、只读 Executor、QuerySpec 语义校验或支付订单口径。
- 不新增数据库表，不修改前端页面，不实现多模型路由、异步任务或并发训练。

## Implementation steps

- [x] 设计并实现模型候选到标准业务概念的规范化逻辑。
- [x] 更新 Intent Prompt，使模型不因预置 ID 词表而丢弃口语化概念。
- [x] 调整模型解析与启发式兜底逻辑，保留低置信澄清。
- [x] 补充订单总数、模型自然语言候选和未知概念的单元测试。
- [x] 补充云端微调模型接入文档。
- [x] 执行 focused pytest、后端全量测试和标准评测。
- [x] 记录模块文档、更新 handoff、独立提交并推送。

## Validation plan

- `py -3 -m pytest backend/tests/test_question_intent_parser.py`
- `npm.cmd run backend:test`
- `npm.cmd run eval:standard`
- 人工检查云端模型配置示例不包含真实密钥。

## Risks

- 小型本地模型仍可能给出空候选或不规范 JSON，因此必须保留确定性兜底和澄清机制。
- 规范化扩展了模型表达自由度，但只能输出项目已定义的受控 ID；新业务指标仍需要先补充指标定义和 QuerySpec。
- 标准评测依赖本地模型，可能超过现有超时窗口；超时必须据实记录，不得标为通过。
