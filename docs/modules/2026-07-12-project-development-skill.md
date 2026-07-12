# 项目开发规范 Skill

## 完成内容

- 在 `.agents/skills/local-data-analysis-development/` 创建项目内开发 Skill。
- 强制开发前阅读 `docs/handoff/current.md`，创建计划并在编码前同步 handoff。
- 强制完成后创建模块记录、更新 handoff、回填计划 checklist 和记录验证结果。
- 固化 API、数据库、SQL/Agent 链路的同步与验证基线。
- 固化中文文本使用 UTF-8 读写，PowerShell 读取显式使用 `-Encoding utf8`。
- 提供 `agents/openai.yaml` UI 元数据。

## 关键决策

- Skill 放在项目 `.agents/skills/`，与仓库一起维护。
- Handoff 只保存当前状态和索引；实现细节、验证和兼容性影响放入计划和模块完成文档。
- 对只读分析和用户明确禁止写文件的请求设置文档例外；紧急修复仍要求最小计划先行。

## 验证

- 已检查 `SKILL.md` 具有有效的 `name`、完整触发描述和无 BOM UTF-8 内容。
- 已检查 `agents/openai.yaml` 包含 display name、25-64 字符的 short description 和 `$local-data-analysis-development` 默认提示。
- `git diff --check` 通过。
- 官方 `quick_validate.py` 未能执行：当前可用 Python 环境缺少 `PyYAML`，报错 `ModuleNotFoundError: No module named 'yaml'`。未安装依赖或修改全局环境。

## 后续事项

- 修复或重建项目 Python 环境后，安装 Skill 工具所需的 `PyYAML` 并重跑官方校验器。
