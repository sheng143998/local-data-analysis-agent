import { MetricCards } from './MetricCards';

type AnswerPanelProps = {
  summary?: string;
};

export function AnswerPanel({ summary }: AnswerPanelProps) {
  return (
    <section className="panel p-5">
      <h3 className="text-lg font-bold text-slate-950">分析总结</h3>
      <p className="mt-3 text-sm leading-7 text-slate-600">
        {summary ??
          '最近 30 天销售额整体呈稳步上升趋势，6 月下旬开始增长更明显。订单数与支付成功率同步改善，退款率维持在 3% 以下，说明增长主要来自有效成交提升，而不是单纯价格波动。'}
      </p>
      <div className="mt-5">
        <MetricCards />
      </div>
    </section>
  );
}
