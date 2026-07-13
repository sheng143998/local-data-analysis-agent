-- 首批契约仅覆盖已验证的基础快照口径；未知概念仍保留开放式模型路径。
INSERT INTO semantic_contracts (
  id, contract_key, version, contract_type, display_name, business_definition,
  source_tables, source_fields, synonyms, time_grain, aggregation, semantic_config, owner, status
)
VALUES
  (gen_random_uuid(), 'user_total', 1, 'metric', '用户总数', '当前可见用户实体的去重总量', ARRAY['users'], ARRAY['users.id'], ARRAY['当前用户总数','当前用户数','总用户数'], '', 'count_distinct', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
  (gen_random_uuid(), 'order_total', 1, 'metric', '订单总数', '当前订单实体的总量', ARRAY['orders'], ARRAY['orders.id'], ARRAY['当前订单总数','总订单数'], '', 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
  (gen_random_uuid(), 'product_total', 1, 'metric', '商品总数', '当前商品实体的总量', ARRAY['products'], ARRAY['products.id'], ARRAY['当前商品总数','总商品数'], '', 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled')
ON CONFLICT (contract_key, version) DO NOTHING;
