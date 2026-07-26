-- 基于结构化真值评测确认的复杂业务口径；仅声明语义合同，不保存可执行 SQL。
INSERT INTO semantic_contracts (
  id, contract_key, version, contract_type, display_name, business_definition,
  source_tables, source_fields, synonyms, default_filters, time_grain,
  aggregation, semantic_config, owner, status
)
VALUES
  (
    gen_random_uuid(), 'paid_order_sales_summary', 1, 'metric', '已支付订单成交额与订单数',
    '成交额按已支付订单计算：先从 payments 按 order_id 去重筛选 status=paid，再关联 orders；销售额累计 orders.total_amount，订单数按 orders.id 去重，避免多条支付记录放大订单金额。',
    ARRAY['orders', 'payments'],
    ARRAY['orders.id', 'orders.purchase_at', 'orders.total_amount', 'payments.order_id', 'payments.status'],
    ARRAY['已支付订单金额', '支付成功订单的销售额', '支付成功订单销售额', '成交额', '成交订单金额'],
    '{"payment_status":"paid"}'::jsonb,
    '',
    'sum',
    '{"replaces_contract_keys":["sales_amount"],"plan":{"measures":[{"name":"sales_amount","operation":"sum"},{"name":"order_count","operation":"count"}],"filters":["payments.status = ''paid''"],"expected_columns":["sales_amount","order_count"],"expected_row_shape":"single"}}'::jsonb,
    'data-team', 'enabled'
  ),
  (
    gen_random_uuid(), 'gross_margin', 1, 'metric', '订单商品整体毛利率',
    '整体毛利率按订单商品明细计算：(SUM(order_items.price) - SUM(product_costs.unit_cost)) / NULLIF(SUM(order_items.price), 0) * 100，并按两位小数输出 gross_margin；不能按单行成本或商品明细列表输出。',
    ARRAY['order_items', 'product_costs'],
    ARRAY['order_items.id', 'order_items.product_id', 'order_items.price', 'product_costs.product_id', 'product_costs.unit_cost'],
    ARRAY['毛利率', '整体毛利率', '订单商品毛利率', '按商品明细计算的毛利率'],
    '{}'::jsonb,
    '',
    'ratio',
    '{"plan":{"measures":[{"name":"gross_margin","operation":"ratio"}],"expected_columns":["gross_margin"],"expected_row_shape":"single"}}'::jsonb,
    'data-team', 'enabled'
  ),
  (
    gen_random_uuid(), 'category_sales_ranking', 2, 'metric', '品类销售额排行',
    '按商品品类汇总订单商品明细售价 SUM(order_items.price)，按销售额降序排序。输出别名必须为 category 和 sales_amount；未要求支付口径时不得关联 payments 或使用 orders.total_amount。',
    ARRAY['order_items', 'products'],
    ARRAY['order_items.price', 'order_items.product_id', 'products.id', 'products.category'],
    ARRAY['销售额最高的品类', '品类销售额排行', '品类卖得最多'],
    '{}'::jsonb,
    '',
    'sum',
    '{"plan":{"measures":[{"name":"sales_amount","operation":"sum"}],"dimensions":["category"],"order_by":["sales_amount DESC"],"limit":5,"expected_columns":["category","sales_amount"],"expected_row_shape":"ranking"}}'::jsonb,
    'data-team', 'enabled'
  )
ON CONFLICT (contract_key, version) DO NOTHING;
