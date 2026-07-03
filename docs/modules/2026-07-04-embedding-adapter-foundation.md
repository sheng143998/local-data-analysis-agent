# 模块：EmbeddingAdapter 基础层

当前状态：代码开发完成，验证已通过，随本次提交完成 commit 和 push，提交信息为 `实现EmbeddingAdapter基础层并通过验证`。

业务逻辑：

本模块新增统一 EmbeddingAdapter，让 schema、metric、SQL Memory 后续生成向量时走统一入口。它支持 OpenAI-compatible `/embeddings` 接口，也支持 deterministic provider 作为本地开发和测试 fallback。普通用户页面不展示 embedding provider、模型名、向量状态或数据库连接状态。

关键代码：

- `backend/app/core/config.py`：新增 `EMBEDDING_PROVIDER`、`EMBEDDING_BASE_URL`、`EMBEDDING_MODEL`、`EMBEDDING_API_KEY`、`EMBEDDING_DIMENSIONS`、`EMBEDDING_TIMEOUT_SECONDS`、`EMBEDDING_MAX_RETRIES`。
- `backend/app/core/embedding_adapter.py`：新增 `EmbeddingAdapter`、`EmbeddingAdapterConfig`、`EmbeddingRequest`、`EmbeddingResponse`、`EmbeddingUsage`。
- `backend/.env.example`：补充 embedding 占位配置，不包含真实密钥。
- `backend/tests/test_embedding_adapter.py`：覆盖 OpenAI-compatible payload、Authorization、空输入、HTTP retry、transport error 和 deterministic 稳定向量。

数据契约：

```python
EmbeddingRequest(texts=["orders total_amount"])
```

返回：

```python
EmbeddingResponse(
    ok=True,
    vectors=[[...]],
    provider="deterministic",
    model="text-embedding-v4",
    dimension=1536,
    latency_ms=0,
)
```

验证：

- `npm run backend:test`：87 passed，1 个 `StarletteDeprecationWarning`，不影响本模块。
- `npm run frontend:build`：已通过。
- `npm run test:e2e`：已通过，question -> FastAPI -> AgentService -> Guard -> Executor -> result。

风险/后续：

- deterministic provider 不是语义 embedding，只是本地 fallback 和测试工具。
- 本模块尚未把向量写入 `schema_metadata`、`metric_definitions` 或 `sql_memories`。
- 下一步需要实现 embedding 同步脚本或 repository 查询，把 pgvector 混合检索接入 schema / metric / memory。
