"""顺序验证一百条多表只读 SQL，并为每条完成状态写入 checkpoint。"""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.tools.sql_execution_tools import execute_guarded_sql, explain_guarded_sql  # noqa: E402
from backend.app.tools.sql_inspector import inspect_query_plan  # noqa: E402
from backend.app.tools.sql_validation_tools import guard_sql  # noqa: E402


DEFAULT_REPORT = ROOT / "eval" / "reports" / "sequential_hundred_query_validation.json"
TOP_N_VALUES = (1, 3, 5, 10, 20, 30, 50, 100, 500, 1000)
YEARS = tuple(range(2016, 2026))
REPEAT_THRESHOLDS = tuple(range(2, 12))
CITY_MIN_ORDERS = (1, 2, 3, 5, 10, 20, 30, 50, 100, 200)


@dataclass(frozen=True)
class QueryCase:
    id: str
    family: str
    sql: str
    query_plan: dict[str, Any]


@dataclass(frozen=True)
class QueryCaseResult:
    id: str
    family: str
    status: str
    inspector_issues: list[str]
    guard_errors: list[str]
    explain_status: str
    execution_status: str
    row_count: int
    latency_ms: int
    sample_row: dict[str, Any] | None


def build_cases() -> list[QueryCase]:
    cases: list[QueryCase] = []
    cases.extend(_paid_order_count_cases())
    cases.extend(_paid_sales_cases())
    cases.extend(_category_sales_cases())
    cases.extend(_category_item_sales_cases())
    cases.extend(_category_margin_cases())
    cases.extend(_refund_rate_cases())
    cases.extend(_city_order_cases())
    cases.extend(_city_average_cases())
    cases.extend(_repeat_user_cases())
    cases.extend(_traffic_conversion_cases())
    if len(cases) != 100 or len({case.id for case in cases}) != 100:
        raise RuntimeError("顺序验证 case 定义必须恰好包含 100 个唯一条目")
    return cases


def run_case(case: QueryCase) -> QueryCaseResult:
    started = perf_counter()
    inspector_issues = [issue.category for issue in inspect_query_plan(case.sql, case.query_plan)]
    if inspector_issues:
        return _result(case, "inspector_rejected", inspector_issues, [], "skipped", "skipped", 0, started, None)

    guard = guard_sql(case.sql)
    if not guard.allowed:
        return _result(case, "guard_blocked", [], guard.errors, "skipped", "skipped", 0, started, None)

    explain = explain_guarded_sql(guard)
    if explain.status != "success":
        return _result(case, "explain_failed", [], [], explain.status, "skipped", 0, started, None)

    execution = execute_guarded_sql(guard)
    status = "passed" if execution.status == "success" else "execution_failed"
    sample_row = execution.rows[0] if execution.rows else None
    return _result(
        case,
        status,
        [],
        [],
        explain.status,
        execution.status,
        execution.row_count,
        started,
        sample_row,
    )


def run_cases_sequentially(cases: list[QueryCase], report_path: Path, *, resume: bool) -> dict[str, Any]:
    completed = _load_checkpoint(report_path) if resume else {}
    for index, case in enumerate(cases, start=1):
        if case.id in completed:
            print(f"[{index}/100] {case.id} checkpoint 已存在，跳过")
            continue
        result = run_case(case)
        completed[case.id] = result
        report = _write_report(report_path, cases, completed, complete=False)
        print(
            f"[{index}/100] {case.id} status={result.status} rows={result.row_count} "
            f"latency={result.latency_ms}ms completed={report['summary']['completed']}"
        )
    return _write_report(report_path, cases, completed, complete=True)


def _result(
    case: QueryCase,
    status: str,
    inspector_issues: list[str],
    guard_errors: list[str],
    explain_status: str,
    execution_status: str,
    row_count: int,
    started: float,
    sample_row: dict[str, Any] | None,
) -> QueryCaseResult:
    return QueryCaseResult(
        id=case.id,
        family=case.family,
        status=status,
        inspector_issues=inspector_issues,
        guard_errors=guard_errors,
        explain_status=explain_status,
        execution_status=execution_status,
        row_count=row_count,
        latency_ms=int((perf_counter() - started) * 1000),
        sample_row=sample_row,
    )


def _paid_order_count_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"paid_order_count_{year}",
            "订单-支付：已支付订单数",
            _paid_scope_sql(year, "COUNT(DISTINCT o.id) AS order_count"),
            _scalar_plan(["orders", "payments"], ["order_count"], ["payments.status = 'paid'"]),
        )
        for year in YEARS
    ]


def _paid_sales_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"paid_sales_{year}",
            "订单-支付：已支付销售额",
            _paid_scope_sql(year, "SUM(o.total_amount) AS sales_amount"),
            _scalar_plan(["orders", "payments"], ["sales_amount"], ["payments.status = 'paid'"]),
        )
        for year in YEARS
    ]


def _category_sales_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"category_sales_top_{limit}",
            "订单商品-商品：品类销售额",
            (
                "SELECT COALESCE(p.category, 'uncategorized') AS category, SUM(oi.price) AS sales_amount "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id "
                "GROUP BY COALESCE(p.category, 'uncategorized') ORDER BY sales_amount DESC "
                f"LIMIT {limit}"
            ),
            _ranking_plan(["order_items", "products"], ["category", "sales_amount"], "sales_amount DESC", limit),
        )
        for limit in TOP_N_VALUES
    ]


def _category_item_sales_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"category_item_sales_top_{limit}",
            "订单-支付-商品明细-商品：品类订单商品数与销售额",
            (
                "SELECT COALESCE(p.category, 'uncategorized') AS category, COUNT(oi.id) AS order_item_count, "
                "SUM(oi.price) AS sales_amount FROM orders o JOIN order_items oi ON oi.order_id = o.id "
                "JOIN products p ON p.id = oi.product_id WHERE EXISTS (SELECT 1 FROM payments pay "
                "WHERE pay.order_id = o.id AND pay.status = 'paid') "
                "GROUP BY COALESCE(p.category, 'uncategorized') ORDER BY order_item_count DESC "
                f"LIMIT {limit}"
            ),
            _ranking_plan(["orders", "payments", "order_items", "products"], ["category", "order_item_count", "sales_amount"], "order_item_count DESC", limit, ["payments.status = 'paid'"]),
        )
        for limit in TOP_N_VALUES
    ]


def _category_margin_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"category_margin_top_{limit}",
            "订单商品-商品-成本：品类毛利率",
            (
                "SELECT COALESCE(p.category, 'uncategorized') AS category, "
                "ROUND((SUM(oi.price) - SUM(pc.unit_cost)) / NULLIF(SUM(oi.price), 0) * 100, 2) AS gross_margin "
                "FROM order_items oi JOIN products p ON p.id = oi.product_id "
                "JOIN product_costs pc ON pc.product_id = oi.product_id "
                "GROUP BY COALESCE(p.category, 'uncategorized') ORDER BY gross_margin DESC "
                f"LIMIT {limit}"
            ),
            _ranking_plan(["order_items", "products", "product_costs"], ["category", "gross_margin"], "gross_margin DESC", limit),
        )
        for limit in TOP_N_VALUES
    ]


def _refund_rate_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"refund_rate_{year}",
            "订单-退款：年度退款订单率",
            (
                "SELECT ROUND(COUNT(DISTINCT r.order_id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate "
                "FROM orders o LEFT JOIN refunds r ON r.order_id = o.id "
                f"WHERE o.purchase_at >= DATE '{year}-01-01' AND o.purchase_at < DATE '{year + 1}-01-01' LIMIT 1"
            ),
            _scalar_plan(["orders", "refunds"], ["refund_rate"]),
        )
        for year in YEARS
    ]


def _city_order_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"city_order_top_{limit}",
            "用户-订单：城市订单数排行",
            (
                "SELECT u.city AS city, COUNT(DISTINCT o.id) AS order_count FROM users u "
                "JOIN orders o ON o.user_id = u.id GROUP BY u.city ORDER BY order_count DESC "
                f"LIMIT {limit}"
            ),
            _ranking_plan(["users", "orders"], ["city", "order_count"], "order_count DESC", limit),
        )
        for limit in TOP_N_VALUES
    ]


def _city_average_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"city_average_min_{minimum}",
            "用户-订单：有最小订单数门槛的城市客单价",
            (
                "SELECT u.city AS city, AVG(o.total_amount) AS avg_order_value, COUNT(DISTINCT o.id) AS order_count "
                "FROM users u JOIN orders o ON o.user_id = u.id GROUP BY u.city "
                f"HAVING COUNT(DISTINCT o.id) >= {minimum} ORDER BY avg_order_value DESC LIMIT 5"
            ),
            _ranking_plan(["users", "orders"], ["city", "avg_order_value", "order_count"], "avg_order_value DESC", 5),
        )
        for minimum in CITY_MIN_ORDERS
    ]


def _repeat_user_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"repeat_users_threshold_{threshold}",
            "用户-订单：复购用户阈值统计",
            (
                "WITH repeat_users AS (SELECT u.id FROM users u JOIN orders o ON o.user_id = u.id "
                f"GROUP BY u.id HAVING COUNT(DISTINCT o.id) >= {threshold}) "
                "SELECT COUNT(*) AS repeat_user_count FROM repeat_users LIMIT 1"
            ),
            _scalar_plan(["users", "orders"], ["repeat_user_count"]),
        )
        for threshold in REPEAT_THRESHOLDS
    ]


def _traffic_conversion_cases() -> list[QueryCase]:
    return [
        QueryCase(
            f"traffic_order_conversion_{year}",
            "流量-订单：年度访问到下单转化率",
            (
                "WITH visitors AS (SELECT COUNT(DISTINCT t.user_id) AS visitor_count FROM traffic_events t "
                f"WHERE t.created_at >= DATE '{year}-01-01' AND t.created_at < DATE '{year + 1}-01-01'), "
                "ordering_visitors AS (SELECT COUNT(DISTINCT o.user_id) AS ordering_user_count FROM orders o "
                "JOIN traffic_events t ON t.user_id = o.user_id) "
                "SELECT ROUND(ordering_visitors.ordering_user_count::numeric / NULLIF(visitors.visitor_count, 0) * 100, 2) "
                "AS visit_to_order_conversion_rate FROM visitors CROSS JOIN ordering_visitors LIMIT 1"
            ),
            _scalar_plan(["traffic_events", "orders"], ["visit_to_order_conversion_rate"]),
        )
        for year in YEARS
    ]


def _paid_scope_sql(year: int, projection: str) -> str:
    return (
        f"SELECT {projection} FROM orders o WHERE EXISTS (SELECT 1 FROM payments p "
        "WHERE p.order_id = o.id AND p.status = 'paid') "
        f"AND o.purchase_at >= DATE '{year}-01-01' AND o.purchase_at < DATE '{year + 1}-01-01' LIMIT 1"
    )


def _scalar_plan(entities: list[str], expected_columns: list[str], filters: list[str] | None = None) -> dict[str, Any]:
    return {"entities": entities, "expected_columns": expected_columns, "filters": filters or []}


def _ranking_plan(
    entities: list[str],
    expected_columns: list[str],
    order_by: str,
    limit: int,
    filters: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "entities": entities,
        "expected_columns": expected_columns,
        "expected_row_shape": "ranking",
        "order_by": [order_by],
        "limit": limit,
        "filters": filters or [],
    }


def _load_checkpoint(path: Path) -> dict[str, QueryCaseResult]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(item["id"]): QueryCaseResult(**item)
        for item in payload.get("cases", [])
        if isinstance(item, dict) and item.get("id")
    }


def _write_report(
    path: Path,
    cases: list[QueryCase],
    completed: dict[str, QueryCaseResult],
    *,
    complete: bool,
) -> dict[str, Any]:
    results = [completed[case.id] for case in cases if case.id in completed]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "strictly_sequential",
        "checkpoint": {"status": "completed" if complete else "running", "completed": len(results), "total": len(cases)},
        "summary": {
            "completed": len(results),
            "passed": sum(result.status == "passed" for result in results),
            "failed": sum(result.status != "passed" for result in results),
        },
        "cases": [asdict(result) for result in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)
    return report


def main() -> None:
    parser = ArgumentParser(description="顺序运行一百条多表 SQL 验证")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    report = run_cases_sequentially(build_cases(), args.report, resume=args.resume)
    print(json.dumps(report["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
