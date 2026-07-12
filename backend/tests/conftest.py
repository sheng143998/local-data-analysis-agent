import pytest

from backend.app.agents import analysis_graph
from backend.app.schemas.sql_generation import GeneratedSql


def _test_sql_for_question(question: str) -> str:
    if "销售额按天变化" in question:
        return """
WITH date_spine AS (
  SELECT generate_series(CURRENT_DATE - INTERVAL '29 days', CURRENT_DATE, INTERVAL '1 day')::date AS order_date
),
daily_orders AS (
  SELECT
    DATE(o.created_at) AS order_date,
    SUM(o.total_amount) AS daily_sales,
    COUNT(DISTINCT o.id) AS order_count
  FROM orders o
  WHERE EXISTS (
    SELECT 1 FROM payments pay
    WHERE pay.order_id = o.id AND pay.status = 'paid'
  )
  GROUP BY DATE(o.created_at)
)
SELECT
  date_spine.order_date,
  COALESCE(daily_orders.daily_sales, 0) AS daily_sales,
  COALESCE(daily_orders.order_count, 0) AS order_count,
  COALESCE(ROUND(daily_orders.daily_sales / NULLIF(daily_orders.order_count, 0), 2), 0) AS avg_order_value
FROM date_spine
LEFT JOIN daily_orders ON daily_orders.order_date = date_spine.order_date
ORDER BY date_spine.order_date DESC
LIMIT 30
"""
    if "每月订单数" in question:
        return """
SELECT
  DATE_TRUNC('month', o.created_at) AS order_month,
  COUNT(DISTINCT o.id) AS order_count
FROM orders o
LEFT JOIN payments pay ON pay.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY DATE_TRUNC('month', o.created_at)
ORDER BY order_month DESC
LIMIT 3
"""
    if "前 10 个商品" in question:
        return """
SELECT
  COALESCE(oi.product_id, 'unknown_product') AS product_label,
  COALESCE(p.category, 'uncategorized') AS product_category,
  SUM(oi.price) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(oi.price) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
LEFT JOIN payments pay ON pay.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY COALESCE(oi.product_id, 'unknown_product'), COALESCE(p.category, 'uncategorized')
ORDER BY daily_sales DESC
LIMIT 10
"""
    if "商品品类销售额最高" in question:
        return """
SELECT
  COALESCE(p.category, 'uncategorized') AS category_label,
  SUM(oi.price) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(oi.price) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
LEFT JOIN payments pay ON pay.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY COALESCE(p.category, 'uncategorized')
ORDER BY daily_sales DESC
LIMIT 10
"""
    if "品类退款率" in question or ("商品品类" in question and "退款率" in question):
        return """
SELECT
  COALESCE(p.category, 'uncategorized') AS category_label,
  SUM(oi.price) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(oi.price) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value,
  ROUND(COUNT(DISTINCT r.id)::numeric / NULLIF(COUNT(DISTINCT o.id), 0) * 100, 2) AS refund_rate
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
LEFT JOIN payments pay ON pay.order_id = o.id
LEFT JOIN refunds r ON r.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY COALESCE(p.category, 'uncategorized')
ORDER BY refund_rate DESC
LIMIT 10
"""
    if "复购率" in question:
        return """
WITH user_order_counts AS (
  SELECT
    o.user_id,
    COUNT(DISTINCT o.id) AS paid_order_count,
    SUM(o.total_amount) AS sales_amount
  FROM orders o
  WHERE o.user_id IS NOT NULL
    AND EXISTS (
      SELECT 1 FROM payments pay
      WHERE pay.order_id = o.id AND pay.status = 'paid'
    )
  GROUP BY o.user_id
)
SELECT
  'repeat_purchase' AS segment_label,
  SUM(user_order_counts.sales_amount) AS daily_sales,
  COUNT(user_order_counts.user_id) AS order_count,
  ROUND(SUM(user_order_counts.sales_amount) / NULLIF(COUNT(user_order_counts.user_id), 0), 2) AS avg_order_value,
  ROUND(COUNT(CASE WHEN user_order_counts.paid_order_count >= 2 THEN user_order_counts.user_id END)::numeric / NULLIF(COUNT(user_order_counts.user_id), 0) * 100, 2) AS repeat_rate
FROM user_order_counts
LIMIT 1
"""
    if "支付方式" in question and "成功率" in question:
        return """
SELECT
  COALESCE(pay.payment_type, 'unknown_method') AS payment_method_label,
  COUNT(DISTINCT pay.id) AS payment_count,
  ROUND(COUNT(CASE WHEN pay.status = 'paid' THEN pay.id END)::numeric / NULLIF(COUNT(pay.id), 0) * 100, 2) AS success_rate
FROM payments pay
GROUP BY COALESCE(pay.payment_type, 'unknown_method')
ORDER BY success_rate DESC
LIMIT 20
"""
    if "毛利率" in question:
        return """
SELECT
  COALESCE(p.category, 'uncategorized') AS category_label,
  SUM(oi.price) AS daily_sales,
  SUM(pc.unit_cost) AS total_cost,
  ROUND((SUM(oi.price) - SUM(pc.unit_cost)) / NULLIF(SUM(oi.price), 0) * 100, 2) AS gross_margin
FROM order_items oi
JOIN orders o ON o.id = oi.order_id
LEFT JOIN products p ON p.id = oi.product_id
LEFT JOIN product_costs pc ON pc.product_id = oi.product_id
LEFT JOIN payments pay ON pay.order_id = o.id
WHERE pay.status = 'paid'
GROUP BY COALESCE(p.category, 'uncategorized')
ORDER BY gross_margin DESC
LIMIT 10
"""
    if "城市" in question and "客单价" in question:
        return """
SELECT
  COALESCE(u.city, 'unknown_city') AS city_label,
  SUM(o.total_amount) AS daily_sales,
  COUNT(DISTINCT o.id) AS order_count,
  ROUND(SUM(o.total_amount) / NULLIF(COUNT(DISTINCT o.id), 0), 2) AS avg_order_value
FROM orders o
LEFT JOIN users u ON u.id = o.user_id
WHERE EXISTS (
  SELECT 1 FROM payments pay
  WHERE pay.order_id = o.id AND pay.status = 'paid'
)
GROUP BY COALESCE(u.city, 'unknown_city')
ORDER BY avg_order_value DESC
LIMIT 30
"""
    return ""


@pytest.fixture(autouse=True)
def stable_model_sql_for_api_tests(monkeypatch, request):
    if not any(test_file in str(request.fspath) for test_file in ("test_api.py", "test_runs.py")):
        yield
        return

    original_select_generated_sql = analysis_graph._select_generated_sql

    def fake_select_generated_sql(
        *,
        question,
        retrieval_context,
        reuse_plan,
        adapter=None,
        model_enabled=None,
        repair_context=None,
    ):
        sql = _test_sql_for_question(question)
        if not sql:
            return original_select_generated_sql(
                question=question,
                retrieval_context=retrieval_context,
                reuse_plan=reuse_plan,
                adapter=adapter,
                model_enabled=False,
                repair_context=repair_context,
            )
        path = "model_rewrite" if reuse_plan.path_type == "rewrite_path" else "model_generate"
        return GeneratedSql(path=path, sql=sql.strip(), model_provider="test", model_name="stub")

    monkeypatch.setattr(analysis_graph, "retrieve_sql_memory", lambda *args, **kwargs: [])
    monkeypatch.setattr(analysis_graph, "_select_generated_sql", fake_select_generated_sql)
    analysis_graph._analysis_graph.cache_clear()
    yield
    analysis_graph._analysis_graph.cache_clear()
