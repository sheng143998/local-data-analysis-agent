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

function displayLabel(field: string, visualization: VisualizationSpec) {
  return visualization.field_labels[field] ?? field.replaceAll('_', ' ');
}

function displayDimension(value: AnalysisRow[string], field: string) {
  const text = String(value ?? '--');
  if (/^\d{4}-\d{2}-\d{2}T/.test(text)) return field.includes('month') ? text.slice(0, 7) : text.slice(0, 10);
  return text;
}

function fieldUnit(field: string, visualization: VisualizationSpec): VisualizationSpec['unit'] {
  return visualization.field_units[field] ?? visualization.unit;
}

function unitLabel(unit: VisualizationSpec['unit']) {
  if (unit === 'currency') return '金额';
  if (unit === 'percent') return '比例';
  return '数量';
}

export function ResultChart({ rows, visualization }: ResultChartProps) {
  const option = useMemo<EChartsOption | null>(() => {
    if (visualization.kind === 'none' || !visualization.x_field || !visualization.y_fields.length) return null;
    const labels = rows.map((row) => displayDimension(row[visualization.x_field!], visualization.x_field!));
    const valueField = visualization.y_fields[0];
    const valueUnit = fieldUnit(valueField, visualization);
    if (visualization.kind === 'pie') {
      return {
        animationDuration: 360,
        color: colors,
        tooltip: { trigger: 'item', valueFormatter: axisFormatter(valueUnit) },
        legend: { type: 'scroll', bottom: 0 },
        series: [{
          type: 'pie',
          radius: ['42%', '70%'],
          name: displayLabel(valueField, visualization),
          data: rows.map((row, index) => ({ name: labels[index], value: numericValue(row[valueField]) ?? 0 })),
          label: { formatter: '{b}: {d}%' },
        }],
      };
    }
    const chartKind: 'line' | 'bar' = visualization.kind === 'line' ? 'line' : 'bar';
    const units = Array.from(new Set(visualization.y_fields.map((field) => fieldUnit(field, visualization))));
    const series = visualization.y_fields.map((field, index) => ({
      name: displayLabel(field, visualization),
      type: chartKind,
      yAxisIndex: units.indexOf(fieldUnit(field, visualization)),
      data: rows.map((row) => numericValue(row[field])),
      smooth: chartKind === 'line',
      showSymbol: chartKind === 'line' ? false : undefined,
      itemStyle: { color: colors[index % colors.length] },
      lineStyle: { width: 2.5 },
      barMaxWidth: 36,
      tooltip: { valueFormatter: axisFormatter(fieldUnit(field, visualization)) },
    }));
    const yAxis = units.map((unit, index) => {
      const fields = visualization.y_fields.filter((field) => fieldUnit(field, visualization) === unit);
      return {
        type: 'value' as const,
        name: fields.length === 1 ? displayLabel(fields[0], visualization) : unitLabel(unit),
        position: index === 0 ? 'left' as const : 'right' as const,
        axisLabel: { formatter: axisFormatter(unit) },
        splitLine: { show: index === 0 },
      };
    });
    return {
      animationDuration: 360,
      color: colors,
      tooltip: { trigger: 'axis' },
      grid: { left: 56, right: units.length > 1 ? 72 : 24, top: 34, bottom: 46, containLabel: true },
      xAxis: { type: 'category', data: labels, axisLabel: { interval: 'auto', hideOverlap: true } },
      yAxis,
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
