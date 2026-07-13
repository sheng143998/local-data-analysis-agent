# SQL Inspector Repair Rule Contract

## Completed behavior

- `InspectionIssue` 现在除 `category` 和 `message` 外带有业务 `repair_rule`，syntax、missing_table、missing_order、missing_limit、time_range 均输出可复制修复指令。
- 时间计划检查要求 SQL 的 WHERE 实际包含计划的两个日期边界，不再把任意业务 WHERE 当作时间过滤。
- SQL generation payload 新增精简 `query_plan` 和 `generation_contract`，明确必需实体、度量、维度、过滤、输出形态，以及召回上下文中的可选表。
- Repair Prompt 优先透传 Inspector 的显式规则，并对已知类别提供保守默认规则；未知类别不猜测公式，仍要求通过 QuerySpec、Guard 和只读 Executor。
- 没有新增固定 SQL、数据库字段、API 字段或安全边界；生成结果继续由既有意图校验、Guard、EXPLAIN 和只读 Executor 处理。

## Key decisions

- 将修复规则放在 Inspector issue 与 repair payload，而不是把业务 SQL 写入代码，保持模型主路径可扩展。
- `query_plan` 是生成必需契约，召回表只作为候选上下文；这样可以降低无关表干扰，但不强制模型 JOIN 所有召回表。
- Repair 规则按类别去重，避免同一轮修复上下文重复消耗小模型窗口。

## API/data-contract impact

- 无公开 API 变化。
- 内部 `InspectionIssue` 增加可选 `repair_rule` 字段；`analysis_graph` 现有 `issue.__dict__` 传递方式保持兼容。
- SQL generator 内部 payload 增加 `query_plan`、`generation_contract` 与分类 `repair_rules`，未持久化完整 prompt 或用户凭据。

## Validation

- `.venv\\Scripts\\python -m pytest backend/tests/test_sql_inspector.py backend/tests/test_model_sql_generator.py -q`：`19 passed`。
- `.venv\\Scripts\\python -m pytest backend/tests/test_analysis_graph_sql_selection.py backend/tests/test_query_planner.py backend/tests/test_sql_validation_tools.py -q`：`49 passed`。
- `git diff --check`：通过（仅有 Git 对工作区换行格式的提示）。
- 未运行 authenticated benchmark，未修改评测报告；主线合并后需统一复测 50-case 基线。

## Remaining risks and follow-up

- 模型仍可能忽略 repair rule 或返回空/错误 SQL；规则不能证明复杂 CTE、子查询和业务聚合语义正确。
- 主线应在同一 authenticated 数据集上比较规则启用前后，并观察 `inspector_issues`、repair 次数、严格成功率和答案匹配率。
- 后续可将 Inspector 的度量/维度/输出列检查进一步 AST 化，但必须先补充误报测试，不能放宽 Guard。

## Delivery

- Commit：待本模块提交后填入。
- Push：待本模块提交后填入。
