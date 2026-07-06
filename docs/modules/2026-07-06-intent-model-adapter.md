# 模块：专用意图识别模型适配

当前状态：已完成专用意图模型配置接入、窄规则收敛和 focused tests 验证。本模块把口语语义理解从 SQL 生成模型中拆出来，支持使用更强的独立意图识别模型，减少为了单个口语 case 增加硬编码规则。

## 业务逻辑

用户输入问题后，后端先调用 `question_intent_parser`：

1. 如果 `INTENT_PARSER_ENABLED=true`，优先使用 `INTENT_MODEL_*` 配置调用专用意图模型。
2. 意图模型输出结构化 JSON：标准指标、标准维度、时间范围、归一化问题、置信度、是否需要澄清。
3. 如果模型不确定或置信度低，后端返回澄清响应，不生成 SQL。
4. 如果模型不可用，保留本地启发式兜底。
5. 归一化问题继续进入原有 RAG、SQL 生成、意图校验、SQL Guard 和只读 Executor。

## 关键代码

- `backend/app/core/config.py`
  - 新增 `INTENT_PARSER_ENABLED`
  - 新增 `INTENT_MODEL_PROVIDER`
  - 新增 `INTENT_MODEL_BASE_URL`
  - 新增 `INTENT_MODEL_NAME`
  - 新增 `INTENT_MODEL_API_KEY`
  - 新增 `INTENT_MODEL_TIMEOUT_SECONDS`
  - 新增 `INTENT_MODEL_MAX_RETRIES`
- `backend/app/tools/question_intent_parser.py`
  - `parse_question_intent()` 改为使用专用意图模型配置。
  - `_intent_model_adapter()` 构造独立 `ModelAdapterConfig`。
  - 移除上一轮针对 `date/month` 的中文关键词二次清洗，改为信任专用意图模型输出。
- `backend/app/tools/model_sql_generator.py`
  - 移除核心汇总问题的强制确定性 SQL 覆盖。
  - 移除 `payments` 条件自动改写为 JOIN 的 case 级修正规则。
  - SQL 生成结果继续交给后续意图校验和 Guard，而不是在生成器里按单个 case 替换。
- `backend/.env.example`
  - 增加 `INTENT_*` 配置示例。

## 数据契约

无数据库结构变更。新增环境变量配置：

```env
INTENT_PARSER_ENABLED=true
INTENT_MODEL_PROVIDER=local
INTENT_MODEL_API_KEY=change_me
INTENT_MODEL_BASE_URL=http://127.0.0.1:11434/v1
INTENT_MODEL_NAME=qwen2.5-coder:7b
INTENT_MODEL_TIMEOUT_SECONDS=10
INTENT_MODEL_MAX_RETRIES=1
```

未配置 `INTENT_*` 时，默认回退到 `MODEL_*` 配置。

## 验证

```powershell
.venv\Scripts\python -m pytest backend\tests\test_question_intent_parser.py backend\tests\test_model_sql_generator.py backend\tests\test_analysis_graph_sql_selection.py
```

结果：

```text
38 passed
```

## 风险和后续

- 更强意图模型只能提升口语理解，不能替代 SQL Guard。
- 如果 SQL 生成模型仍较弱，仍可能生成错误 SQL；后续应继续通过意图校验、字段校验、Guard 和评估集定位。
- 建议实际配置更强的 intent 模型，例如 `qwen-plus`、`gpt-4.1-mini` 或其它 OpenAI-compatible 的中文语义模型。
