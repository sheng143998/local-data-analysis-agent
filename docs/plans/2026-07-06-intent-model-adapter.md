# 专用意图识别模型适配计划

## Goal

当前自然语言问题会先经过轻量意图解析器，再进入 RAG、SQL 生成、意图校验、SQL Guard 和 Executor。上一轮为了弥补小模型误判，临时增加了年份维度清洗、核心汇总确定性 SQL 等较窄规则。后续应改为使用专门的意图识别模型承担口语语义理解，减少针对单个 case 的规则补丁。

## Scope

包含：
- 新增独立 `INTENT_*` 模型配置，允许意图识别模型和 SQL 生成模型分开部署。
- `question_intent_parser` 优先使用专用意图模型；未配置时回退到现有 `MODEL_*` 配置。
- 保留 LLM 失败后的本地启发式兜底和低置信反问能力。
- 移除过窄的意图后处理规则，例如把模型输出的 `date/month` 维度按中文关键词再次过滤。
- 移除核心汇总题的强制确定性 SQL 覆盖，让专用意图模型负责准确归一化，后续 SQL 仍经过意图校验和 Guard。
- 更新 focused tests 和配置示例。

不包含：
- 不移除 SQL Guard / 字段白名单 / 只读校验。
- 不让意图模型直接放行 SQL。
- 不改前端页面结构。
- 不配置真实生产 API key。

## Module boundary

上游输入：
- 用户原始自然语言问题。
- `.env` 中的 `INTENT_MODEL_*` 配置。

下游输出：
- `ParsedQuestionIntent.normalized_question`
- `metrics`
- `dimensions`
- `time_range`
- `confidence`
- `needs_clarification`
- `clarification`

## Implementation steps

- [x] 创建计划文档。
- [x] 扩展后端配置和 `.env.example`。
- [x] 让 `question_intent_parser` 使用专用意图模型配置。
- [x] 移除上一轮过窄意图清洗和核心汇总 SQL 兜底。
- [x] 更新测试。
- [x] 运行 focused tests。
- [x] 补模块完成文档。

## Validation plan

- `.venv\Scripts\python -m pytest backend/tests/test_question_intent_parser.py backend/tests/test_model_sql_generator.py backend/tests/test_analysis_graph_sql_selection.py`

## Risks

- 更强意图模型能减少口语误判，但不能保证 SQL 生成永远正确；SQL 仍必须经过意图校验、SQL Guard 和只读 Executor。
- 未配置真实 `INTENT_MODEL_*` 时，系统会回退到现有模型或本地启发式，质量取决于本地模型能力。
