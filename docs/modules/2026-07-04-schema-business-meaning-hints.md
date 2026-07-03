# 模块：Schema 字段业务含义提示

当前状态：本模块已完成字段名启发式说明生成、完整验证、commit 和 push。提交信息为 `增强Schema字段业务含义提示并通过验证`，已推送到 GitHub。它不新增固定 SQL 模板，不调用外部模型，不改变普通用户前端。

业务逻辑：开发者换库、导入新表或新增字段后，运行 `sync_schema_metadata.py` 或 `context:refresh` 时，系统会为新增或空说明字段生成基础中文说明。例如 `total_amount` 会被识别为金额字段，`user_id` 会被识别为关联用户实体的标识，`city` 会被识别为地域维度字段。已有人工 `description` 和 `business_meaning` 继续保留，不会被覆盖。

关键代码：

- `backend/app/services/schema_sync_service.py`
  - `infer_schema_description()`：生成 `table.column + 字段类型标签 + data_type` 的字段说明。
  - `infer_schema_business_meaning()`：按字段名和类型生成基础中文业务含义。
  - `_column_label()`、`_data_type_hint()`：封装常见字段名和类型提示。
  - `_upsert_schema_metadata()`：写入推断说明，并继续只在已有说明为空时补齐。
- `backend/tests/test_schema_sync_service.py`
  - 覆盖 upsert 参数、金额字段、外键字段、时间字段、地域和分类维度字段。

数据契约：

- 数据库结构不变。
- 写入内容增强：
  - `schema_metadata.description`
  - `schema_metadata.business_meaning`
- 保留策略不变：
  - `schema_metadata.description = ''` 时才写入推断说明。
  - `schema_metadata.business_meaning = ''` 时才写入推断含义。

验证：

- `py -3 -m pytest backend/tests/test_schema_sync_service.py backend/tests/test_embedding_sync_service.py`，33 passed。
- `npm run backend:test`，141 passed，1 个 `StarletteDeprecationWarning`。
- `npm run eval:standard`，20/20 链路成功，严格成功率 55%。
- `npm run frontend:build` 已通过。
- `npm run test:e2e` 已通过，1 个 `StarletteDeprecationWarning`。

风险/后续：

- 字段名启发式不能替代人工业务口径，后续可做 schema 说明编辑接口或离线模型补全。
- 非英文、缩写严重或非常规字段名只能得到通用说明。
