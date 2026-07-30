# GitHub 首页 README 更新

## Goal

基于当前代码、配置、路由和评测工具重写根目录 README，使 GitHub 访客能快速理解项目解决的问题、核心技术差异、实际功能和可复现方式。

## Scope

- 重写根目录 `README.md` 的信息结构和文案。
- 核对技术栈、Agent 链路、产品页面、启动命令、评测命令和文档链接。
- 更新本次任务的 handoff 与模块记录。

## Out of scope

- 不修改应用代码、API、数据库结构、配置行为或评测逻辑。
- 不生成或提交产品截图，不写入未经仓库报告支持的效果数据。
- 不处理工作区中已有的业务代码改动。

## Implementation steps

- [x] 读取 handoff、现有 README、代码结构、路由、配置和核心架构文档。
- [x] 重写 README 的项目定位、能力、架构、运行与验证说明。
- [x] 校验 README 中的相对链接、目录和 npm scripts。
- [x] 创建模块记录并更新 handoff。

## Validation plan

- 使用 UTF-8 重新读取 README 和新增文档。
- 静态检查 README 引用的本地路径和 `package.json` scripts。
- 运行 `git diff --check` 检查 Markdown 格式问题。

## Risks

- 工作区已有大量未提交代码变更，本次只操作 README 和本任务文档，不能混入或覆盖其他修改。
- 评测结果会随模型和数据变化，GitHub 首页不展示容易失效的阶段性百分比，只提供可复现命令和报告入口。
