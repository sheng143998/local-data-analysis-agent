-- 基础实体快照总量的受审核业务定义；不包含可执行 SQL 模板。
INSERT INTO semantic_contracts (id, contract_key, version, contract_type, display_name, business_definition, source_tables, source_fields, synonyms, aggregation, semantic_config, owner, status)
VALUES
 (gen_random_uuid(), 'order_item_total', 1, 'metric', '订单商品明细总数', '订单商品明细记录总量', ARRAY['order_items'], ARRAY['order_items.id'], ARRAY['当前订单商品明细总数','订单商品明细总数'], 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
 (gen_random_uuid(), 'payment_record_total', 1, 'metric', '支付记录总数', '支付记录总量', ARRAY['payments'], ARRAY['payments.id'], ARRAY['当前支付记录总数','支付记录总数'], 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
 (gen_random_uuid(), 'refund_record_total', 1, 'metric', '退款记录总数', '退款记录总量', ARRAY['refunds'], ARRAY['refunds.id'], ARRAY['当前退款记录总数','退款记录总数'], 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
 (gen_random_uuid(), 'review_total', 1, 'metric', '评价总数', '评价记录总量', ARRAY['reviews'], ARRAY['reviews.id'], ARRAY['当前评价总数','评价总数'], 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
 (gen_random_uuid(), 'traffic_event_total', 1, 'metric', '流量事件总数', '流量事件记录总量', ARRAY['traffic_events'], ARRAY['traffic_events.id'], ARRAY['当前流量事件总数','流量事件总数'], 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
 (gen_random_uuid(), 'coupon_total', 1, 'metric', '优惠券总数', '优惠券记录总量', ARRAY['coupons'], ARRAY['coupons.id'], ARRAY['当前优惠券总数','优惠券总数'], 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled'),
 (gen_random_uuid(), 'coupon_usage_total', 1, 'metric', '优惠券使用记录总数', '优惠券使用记录总量', ARRAY['coupon_usages'], ARRAY['coupon_usages.id'], ARRAY['当前优惠券使用记录总数','优惠券使用记录总数'], 'count', '{"time_semantics":"snapshot"}'::jsonb, 'data-team', 'enabled')
ON CONFLICT (contract_key, version) DO NOTHING;
