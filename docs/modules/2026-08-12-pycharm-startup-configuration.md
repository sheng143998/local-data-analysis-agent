# PyCharm 启动配置

## 完成内容

- 将后端 FastAPI、pytest、Context Refresh、标准评测和 E2E 配置的 Python 解释器改为当前工作区 `.venv\Scripts\python.exe`。
- 保留前端 `npm run dev` 配置。
- 新增 `Start All (Backend + Frontend)` 组合配置，可同时启动后端 `127.0.0.1:8000` 和前端开发服务器。
- 未修改 `backend/.env`，没有把本地数据库、模型或评测凭据写入配置文件。

## 关键决策

- 使用绝对解释器路径，避免 PyCharm 继续引用已不存在的旧工作区目录。
- 运行配置保留在 `.idea/runConfigurations/`；该目录已被 `.gitignore` 忽略，因此属于本机 IDE 配置，不会提交到仓库。

## API/数据契约影响

无。未修改应用代码、API、数据库迁移或本地环境变量。

## 验证

- 所有共享运行配置 XML 解析通过，旧工作区路径检查通过。
- `C:\Users\admin\Desktop\数据分析agent\.venv\Scripts\python.exe -c "import backend.app.main"` 通过。
- `npm.cmd --prefix frontend run build` 通过。
- `git diff --check` 通过。

## 剩余风险

- 一键启动只负责启动进程；后端实际分析仍依赖 PostgreSQL，以及按本地 `.env` 配置的 Redis、模型和 Embedding 服务。
- 前端构建存在 Vite 大 chunk warning，不影响本次启动配置。

## 后续工作

- 在 PyCharm 中选择 `Start All (Backend + Frontend)` 运行；首次运行若提示 Node interpreter，选择系统 Node.js/npm。
