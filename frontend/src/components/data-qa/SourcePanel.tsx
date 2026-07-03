export function SourcePanel() {
  const items = [
    ['数据集', 'Olist 巴西电商公开数据集 + 合成增强数据'],
    ['数据表', 'orders、order_items、payments、refunds'],
    ['字段', 'created_at、status、total_amount'],
    ['指标口径', '销售额 = 已支付订单 total_amount 汇总'],
    ['数据时间范围', '2026-06-03 至 2026-07-03'],
    ['返回行数', '1,240'],
    ['查询耗时', '120ms'],
    ['SQL 安全', '只读 SELECT'],
  ];
  return (
    <section className="panel p-5">
      <h3 className="text-lg font-bold text-slate-950">数据来源与指标口径</h3>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {items.map(([label, value]) => (
          <div key={label} className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3 text-sm">
            <span className="text-slate-500">{label}</span>
            <span className="text-right font-medium text-slate-800">{value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
