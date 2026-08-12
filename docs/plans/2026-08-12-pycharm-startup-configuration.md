# PyCharm 启动配置

## Goal

修正项目现有 PyCharm 运行配置，使后端、前端和常用验证任务使用当前工作区路径，并提供一个可直接启动前后端的组合配置。

## Scope

- 更新 `.idea/runConfigurations/` 中 Python 配置的解释器路径和模块引用。
- 保留前端现有 npm 启动方式。
- 新增前后端组合启动配置。
- 验证配置文件、Python 导入和前端依赖。

## Out of scope

- 不修改业务代码、数据库结构、模型配置或密钥。
- 不提交 `backend/.env` 或任何本地运行凭据。

## Implementation steps

- [x] 修正现有 PyCharm Python 运行配置的路径。
- [x] 新增前后端一键启动组合配置。
- [x] 校验运行配置 XML、Python 解释器和前端依赖。
- [x] 更新模块记录和当前 handoff。

## Validation plan

- 检查所有共享运行配置中的旧工作区路径已清除。
- 使用项目 `.venv` 验证后端模块可导入。
- 使用前端 npm 依赖执行生产构建。
- 使用 `git diff --check` 检查文档和配置格式。

## Risks

- 后端启动仍依赖 PostgreSQL、Redis（如启用）和本地模型/Embedding 配置；PyCharm 配置只能解决启动入口，不能替代这些外部服务。
- 前端和后端需要分别保持运行，组合配置会同时启动两个进程。
