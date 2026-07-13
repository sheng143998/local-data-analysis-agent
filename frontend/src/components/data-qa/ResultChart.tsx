import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { Chart } from '../common/Chart';
import type { AnalysisRow, VisualizationSpec } from '../../types/analysis';

type ResultChartProps = {
  rows: AnalysisRow[];
  visualization: VisualizationSpec;
};

const colors = ['#0f766e', '#2563eb', '#d97706', '#be123c'];

function numericValue(value: AnalysisRow[string]) {
  if (typeof value === 'number') return value;
  if (typeof value === 'string' && value.trim() !== '' && Number.isFinite(Number(value))) return Number(value);
  return null;
}

function axisFormatter(unit: VisualizationSpec['unit']) {
  if (unit === 'currency') return (value: unknown) => `¥${Number(value).toLocaleString()}`;
  if (unit === 'percent') return (value: unknown) => `${Number(value)}%`;
  return (value: unknown) => Number(value).toLocaleString();
}

export function ResultChart({ rows, visualization }: ResultChartProps) {
  const option = useMemo<EChartsOption | null>(() => {
    if (visualization.kind === 'none' || !visualization.x_field || !visualization.y_fields.length) return null;
    const labels = rows.map((row) => String(row[visualization.x_field!] ?? '--'));
    const valueField = visualization.y_fields[0];
    if (visualization.kind === 'pie') {
      return {
        animationDuration: 360,
        color: colors,
        tooltip: { trigger: 'item', valueFormatter: axisFormatter(visualization.unit) },
        legend: { type: 'scroll', bottom: 0 },
        series: [{
          type: 'pie',
          radius: ['42%', '70%'],
          data: rows.map((row, index) => ({ name: labels[index], value: numericValue(row[valueField]) ?? 0 })),
          label: { formatter: '{b}: {d}%' },
        }],
      };
    }
    const chartKind: 'line' | 'bar' = visualization.kind === 'line' ? 'line' : 'bar';
    const series = visualization.y_fields.map((field, index) => ({
      name: field.replaceAll('_', ' '),
      type: chartKind,
      data: rows.map((row) => numericValue(row[field])),
      smooth: chartKind === 'line',
      showSymbol: chartKind === 'line' ? false : undefined,
      itemStyle: { color: colors[index % colors.length] },
      lineStyle: { width: 2.5 },
      barMaxWidth: 36,
    }));
    return {
      animationDuration: 360,
      color: colors,
      tooltip: { trigger: 'axis', valueFormatter: axisFormatter(visualization.unit) },
      grid: { left: 56, right: 24, top: 34, bottom: 46, containLabel: true },
      xAxis: { type: 'category', data: labels, axisLabel: { interval: 'auto', hideOverlap: true } },
      yAxis: { type: 'value', axisLabel: { formatter: axisFormatter(visualization.unit) } },
      series,
    };
  }, [rows, visualization]);

  if (!option) return null;
  return (
    <section className="overflow-hidden border border-slate-200 bg-white" style={{ borderRadius: 8 }}>
      <div className="border-b border-slate-200 px-4 py-3 text-sm font-semibold text-slate-900">{visualization.title}</div>
      <div className="p-3"><Chart option={option} height={300} /></div>
    </section>
  );
}
