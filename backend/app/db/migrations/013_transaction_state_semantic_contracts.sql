-- 订单与支付状态的审核业务口径；仅声明来源、粒度和结果形态，不保存可执行 SQL。
INSERT INTO semantic_contracts (
  id, contract_key, version, contract_type, display_name, business_definition,
  source_tables, source_fields, synonyms, aggregation, semantic_config, owner, status
)
VALUES
  (
    gen_random_uuid(), 'order_status_distribution', 1, 'metric', '各订单状态数量',
    '按 orders.status 分组统计订单实体数量；每条订单只计为一个订单状态记录。',
    ARRAY['orders'], ARRAY['orders.id', 'orders.status'],
    ARRAY['各订单状态数量', '订单状态分布', '订单状态统计', '不同订单状态的订单数'],
    'count',
    '{"plan":{"measures":[{"name":"order_status_count","operation":"count"}],"dimensions":["order_status"],"expected_columns":["order_status","order_status_count"],"expected_row_shape":"grouped"}}'::jsonb,
    'data-team', 'enabled'
  ),
  (
    gen_random_uuid(), 'payment_status_distribution', 1, 'metric', '各支付状态数量',
    '按 payments.status 分组统计支付记录数量；支付状态只来自支付记录表。',
    ARRAY['payments'], ARRAY['payments.id', 'payments.status'],
    ARRAY['各支付状态数量', '支付状态分布', '支付状态统计', '不同支付状态的支付记录数'],
    'count',
    '{"plan":{"measures":[{"name":"payment_status_count","operation":"count"}],"dimensions":["payment_status"],"expected_columns":["payment_status","payment_status_count"],"expected_row_shape":"grouped"}}'::jsonb,
    'data-team', 'enabled'
  ),
  (
    gen_random_uuid(), 'payment_method_record_count', 1, 'metric', '各支付方式记录数',
    '按 payments.payment_type 分组统计支付记录数量，不把支付方式记录数误当成订单数。',
    ARRAY['payments'], ARRAY['payments.id', 'payments.payment_type'],
    ARRAY['各支付方式记录数', '支付方式记录数', '支付方式统计', '不同支付方式的支付记录数'],
    'count',
    '{"plan":{"measures":[{"name":"payment_method_count","operation":"count"}],"dimensions":["payment_method"],"expected_columns":["payment_method","payment_method_count"],"expected_row_shape":"grouped"}}'::jsonb,
    'data-team', 'enabled'
  ),
  (
    gen_random_uuid(), 'payment_method_paid_amount', 1, 'metric', '各支付方式已支付金额',
    '按 payments.payment_type 分组累计支付记录 amount，且只统计 payments.status = paid 的记录。',
    ARRAY['payments'], ARRAY['payments.payment_type', 'payments.amount', 'payments.status'],
    ARRAY['各支付方式已支付金额', '支付方式已支付金额', '不同支付方式的已支付金额', '支付方式成交金额'],
    'sum',
    '{"plan":{"measures":[{"name":"payment_method_paid_amount","operation":"sum"}],"dimensions":["payment_method"],"filters":["payments.status = ''paid''"],"expected_columns":["payment_method","payment_method_paid_amount"],"expected_row_shape":"grouped"}}'::jsonb,
    'data-team', 'enabled'
  )
ON CONFLICT (contract_key, version) DO NOTHING;
