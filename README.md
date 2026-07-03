# 本地数据分析 Agent

本项目是一个本地化 AI 数据分析系统。用户可以像聊天一样提出业务问题，系统后端负责生成或复用 SQL、校验安全规则、执行只读查询，并返回自然语言结论、SQL、结果表和数据来源。

## 当前结构

```text
frontend/   React + Vite + TypeScript 前端
backend/    FastAPI 后端
docs/       架构、计划和研发文档
```

## 常用命令

```bash
npm run frontend:build
npm run backend:test
npm run test:e2e
```

## 当前状态

- 已完成前端/后端目录拆分。
- 已完成 FastAPI mock 最小闭环。
- 已完成聊天式数据问答页面。
- 已完成指标口径前端 CRUD。
- 后续优先推进 PostgreSQL migrations、指标后端 CRUD、SQL Guard 与只读 Executor。
