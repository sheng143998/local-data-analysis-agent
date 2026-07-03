# Backend

本目录承载本地数据分析 Agent 的 FastAPI 后端。

当前最小闭环：

1. `POST /api/analyze` 接收自然语言问题。
2. `AgentService` 调用 mock Agent graph。
3. graph 经过工具层生成只读 SQL、mock 查询结果和来源信息。
4. API 返回前端需要展示的分析摘要、SQL、表格数据和追溯信息。

后续真实能力会逐步替换 mock：

- `agents/`: LangGraph 节点与路由
- `tools/`: SQL 生成、校验、Guard、执行器、SQL Memory 检索
- `db/`: PostgreSQL/pgvector 连接、迁移、仓储
- `services/`: 业务编排与响应塑形
- `schemas/`: Pydantic API 契约
