from typing import Literal


PathType = Literal["fast_path", "rewrite_path", "cold_path"]


GENERATED_SQL = """SELECT
  DATE(o.created_at) AS order_date,
  SUM(o.total_amount) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
LEFT JOIN payments p ON p.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE o.created_at >= '2026-06-03'
  AND o.created_at < '2026-07-04'
  AND p.status = 'paid'
GROUP BY DATE(o.created_at)
ORDER BY order_date ASC
LIMIT 1240;"""


def build_mock_rows() -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for index in range(30):
        day = index + 4
        amount = 182000 + index * 6200
        orders = 920 + index * 18
        rows.append(
            {
                "date": f"2026-06-{day:02d}",
                "amount": amount,
                "orders": orders,
                "avg": round(amount / orders),
                "refundRate": f"{2.1 + (index % 4) * 0.2:.1f}%",
            }
        )
    return rows


def build_mock_analysis(question: str, path: PathType) -> dict:
    return {
        "question": question,
        "path": path,
        "summary": "最近 30 天销售额整体呈稳步上升趋势，订单数同步改善，退款率维持在 3% 以下。",
        "sql": GENERATED_SQL,
        "metrics": [
            {"label": "总销售额", "value": "¥ 732.6 万", "delta": "+12.4%", "hint": "环比上升"},
            {"label": "订单数", "value": "28,436", "delta": "+8.7%", "hint": "近 30 天"},
            {"label": "退款率", "value": "2.8%", "delta": "-0.4%", "hint": "风险下降"},
            {"label": "支付成功率", "value": "97.6%", "delta": "+1.3%", "hint": "网关稳定"},
        ],
        "rows": build_mock_rows(),
        "source": {
            "dataset": "Olist 巴西电商公开数据集 + 合成增强数据",
            "tables": ["orders", "order_items", "payments", "refunds"],
            "fields": ["created_at", "status", "total_amount"],
            "metricDefinition": "销售额 = 已支付订单 total_amount 汇总",
            "range": "2026-06-03 至 2026-07-03",
            "returnedRows": 1240,
            "queryTime": "120ms",
            "security": "只读 SELECT",
        },
        "trace": {
            "toolCalls": 4,
            "modelCalls": 0,
            "memoryCandidates": 12,
            "totalTime": "912ms",
        },
        "steps": [
            {"name": "理解问题", "status": "已完成", "time": "36ms"},
            {"name": "查找相似问题", "status": "已完成", "time": "45ms"},
            {"name": "读取数据结构", "status": "已完成", "time": "52ms"},
            {"name": "生成 SQL", "status": "已完成", "time": "418ms"},
            {"name": "安全校验", "status": "已完成", "time": "83ms"},
            {"name": "执行查询", "status": "已完成", "time": "120ms"},
            {"name": "整理结论", "status": "已完成", "time": "158ms"},
        ],
    }
