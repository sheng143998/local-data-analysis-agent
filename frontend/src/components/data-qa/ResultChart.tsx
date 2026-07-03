import { Chart } from '../common/Chart';
import { salesTrend } from '../../data/mock';

export function ResultChart() {
  return (
    <section className="panel p-5">
      <h3 className="text-lg font-bold text-slate-950">最近 30 天销售趋势</h3>
      <Chart
        height={320}
        option={{
          animationDuration: 900,
          tooltip: { trigger: 'axis' },
          grid: { left: 44, right: 24, top: 38, bottom: 36 },
          xAxis: { type: 'category', data: salesTrend.map((item) => item.date.slice(5)), boundaryGap: false },
          yAxis: { type: 'value', axisLabel: { formatter: (value: number) => `${Math.round(value / 10000)}万` } },
          series: [
            {
              name: '日销售额',
              type: 'line',
              smooth: true,
              showSymbol: false,
              data: salesTrend.map((item) => item.amount),
              lineStyle: { color: '#0891b2', width: 3 },
              areaStyle: { color: 'rgba(34, 211, 238, 0.16)' },
            },
          ],
        }}
      />
    </section>
  );
}
