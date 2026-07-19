INSERT INTO semantic_contracts (
  id, contract_key, version, contract_type, display_name, business_definition,
  source_tables, source_fields, synonyms, default_filters, time_grain,
  aggregation, semantic_config, owner, status
)
SELECT
  gen_random_uuid(),
  'category_item_sales_ranking',
  1,
  'metric',
  '品类订单商品数与销售额排行',
  '在已支付订单范围内，按商品品类汇总订单商品明细数量和明细售价；销售额使用 order_items.price，不能把整单 orders.total_amount 重复分配到多个品类。',
  ARRAY['orders', 'payments', 'order_items', 'products'],
  ARRAY['orders.id', 'payments.order_id', 'payments.status', 'order_items.id', 'order_items.order_id', 'order_items.price', 'order_items.product_id', 'products.id', 'products.category'],
  ARRAY['订单商品数量最多的品类', '订单商品数和销售额最多的品类', '品类订单商品数与销售额排行'],
  '{"payment_status":"paid"}'::jsonb,
  '',
  'sum',
  '{"required_question_terms":["订单商品","销售额"],"replaces_contract_keys":["sales_amount","category_item_count_ranking"],"plan":{"measures":[{"name":"order_item_count","operation":"count"},{"name":"sales_amount","operation":"sum"}],"dimensions":["category"],"filters":["payments.status = ''paid''"],"order_by":["order_item_count DESC"],"expected_columns":["category","order_item_count","sales_amount"],"expected_row_shape":"ranking"}}'::jsonb,
  'data-team',
  'enabled'
WHERE NOT EXISTS (
  SELECT 1
  FROM semantic_contracts
  WHERE contract_key = 'category_item_sales_ranking' AND version = 1
);
