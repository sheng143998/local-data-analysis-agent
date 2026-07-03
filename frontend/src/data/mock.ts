export const salesTrend = Array.from({ length: 30 }, (_, index) => {
  const day = index + 4;
  const amount = 182000 + index * 6200 + Math.round(Math.sin(index / 2) * 18000);
  const orders = 920 + index * 18 + Math.round(Math.cos(index / 3) * 60);
  return {
    date: `2026-06-${String(day).padStart(2, '0')}`,
    amount,
    orders,
    avg: Math.round(amount / orders),
    refundRate: `${(2.1 + Math.sin(index / 4) * 0.6).toFixed(1)}%`,
  };
});

export const metricCards = [
  { label: '总销售额', value: '¥ 732.6 万', delta: '+12.4%', hint: '环比上升', color: 'emerald' },
  { label: '订单数', value: '28,436', delta: '+8.7%', hint: '近 30 天', color: 'cyan' },
  { label: '退款率', value: '2.8%', delta: '-0.4%', hint: '风险下降', color: 'amber' },
  { label: '支付成功率', value: '97.6%', delta: '+1.3%', hint: '网关稳定', color: 'emerald' },
];

export const pipelineSteps = [
  { name: '理解问题', status: '已完成', time: '36ms' },
  { name: '检索 SQL 记忆', status: '已完成', time: '45ms' },
  { name: '检索数据结构', status: '已完成', time: '52ms' },
  { name: '生成 SQL', status: '已完成', time: '418ms' },
  { name: '校验 SQL', status: '已完成', time: '83ms' },
  { name: '执行查询', status: '运行中', time: '120ms' },
  { name: '总结结果', status: '已跳过', time: '--' },
];

export const finalSql = `SELECT
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
LIMIT 1240;`;

export const historyRows = [
  ['最近 30 天销售额按天变化如何？', 'rewrite_path', 'orders, payments, refunds', '120ms', '执行成功', '2026-07-03 12:20'],
  ['哪个商品品类退款率最高？', 'cold_path', 'products, refunds', '246ms', '执行成功', '2026-07-03 11:12'],
  ['按月查看新增用户趋势', 'fast_path', 'users', '88ms', '执行成功', '2026-07-02 19:45'],
  ['支付失败率异常来自哪个渠道？', 'rewrite_path', 'payments, traffic_events', '310ms', '执行失败', '2026-07-02 16:08'],
  ['优惠券带来的复购率提升多少？', 'cold_path', 'coupons, coupon_usages, orders', '288ms', '执行成功', '2026-07-01 09:41'],
];

export const sourceRows = [
  ['users', '用户主档与注册渠道', '1,284,900', '2026-07-03 12:10', '已向量化'],
  ['products', '商品资料、品类、成本区间', '84,212', '2026-07-03 11:40', '已向量化'],
  ['orders', '订单主表与状态流转', '3,918,204', '2026-07-03 12:14', '已向量化'],
  ['order_items', '订单明细、件数与单价', '8,240,113', '2026-07-03 12:14', '已向量化'],
  ['payments', '支付渠道、状态与金额', '3,902,887', '2026-07-03 12:14', '已向量化'],
  ['refunds', '退款记录与原因', '211,420', '2026-07-03 10:52', '已向量化'],
  ['traffic_events', '访问、搜索、加购行为', '18,420,000', '2026-07-03 11:22', '未向量化'],
  ['coupons', '优惠券配置', '1,280', '2026-07-02 18:12', '已向量化'],
  ['coupon_usages', '优惠券核销记录', '624,812', '2026-07-03 09:30', '已向量化'],
  ['reviews', '评价文本与评分', '980,451', '2026-07-02 23:20', '已向量化'],
  ['inventory_snapshots', '库存快照', '4,800,000', '2026-07-03 08:00', '未向量化'],
  ['product_costs', '商品成本与毛利辅助表', '84,212', '2026-07-02 21:31', '已向量化'],
];

export const metricDefinitions = [
  ['销售额', '已支付订单 total_amount 汇总', 'SUM(orders.total_amount)', 'orders, payments', 'total_amount, status', '最近 7 天销售额是多少？'],
  ['订单数', '去重后的有效订单数量', 'COUNT(DISTINCT orders.id)', 'orders', 'id, status', '本月订单数较上月变化？'],
  ['客单价', '销售额除以订单数', '销售额 / 订单数', 'orders', 'total_amount', '最近 30 天平均客单价？'],
  ['退款率', '退款订单数占有效订单数比例', 'refund_orders / paid_orders', 'refunds, orders', 'order_id, status', '哪个品类退款率最高？'],
  ['支付成功率', '成功支付笔数占支付发起笔数比例', 'paid / attempted', 'payments', 'status', '最近 30 天支付失败率？'],
  ['复购率', '周期内多次下单用户占比', 'repeat_users / active_users', 'users, orders', 'user_id, created_at', '复购率最高的用户来源？'],
  ['毛利率', '销售毛利占销售额比例', '(sales - cost) / sales', 'product_costs, order_items', 'cost, price', '哪个品类毛利率最高？'],
  ['转化率', '下单用户占访问用户比例', 'buyers / visitors', 'traffic_events, orders', 'event_type, user_id', '搜索流量转化率如何？'],
];

export const sqlMemoryRows = [
  ['最近 N 天销售趋势', 'sales_trend', 'orders, payments', '86', '2', '94ms', '2026-07-03 12:20'],
  ['品类退款率排行', 'refund_rank', 'products, refunds', '42', '4', '132ms', '2026-07-03 11:12'],
  ['支付失败率分析', 'payment_failure', 'payments', '31', '5', '118ms', '2026-07-02 16:08'],
  ['新增用户月趋势', 'user_growth', 'users', '59', '1', '72ms', '2026-07-02 19:45'],
];

export const failureRows = [
  ['支付失败率异常来自哪个渠道？', '字段 channel_name 未匹配到白名单', 'SELECT channel_name, COUNT(*) FROM payments ...', '待修复'],
  ['库存周转天数按品牌排序', '指标口径缺少库存均值定义', 'SELECT brand, inventory_days FROM ...', '处理中'],
  ['优惠券 ROI 按活动拆分', '缺少 campaign_id 关联路径', 'SELECT campaign_id, revenue / cost ...', '已修复'],
];

export const pathShare = [
  { value: 48, name: 'fast_path' },
  { value: 34, name: 'rewrite_path' },
  { value: 18, name: 'cold_path' },
];
