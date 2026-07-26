import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { BarChart, LineChart, PieChart } from 'echarts/charts';
import type { BarSeriesOption, LineSeriesOption, PieSeriesOption } from 'echarts/charts';
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components';
import type { GridComponentOption, LegendComponentOption, TooltipComponentOption } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 仅注册当前应用（ResultChart / EvaluationDashboard）实际用到的图表与组件。
echarts.use([LineChart, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

// 暖色主题：分类色板贴合纸感界面，轴线弱化、柱条圆角、白底软阴影 tooltip。
// 业务组件无需感知，统一由本包装组件应用。
const warmTheme = {
  color: ['#C96442', '#7D9B76', '#D4A27F', '#8B7E74', '#A8763E', '#5E7B8B'],
  textStyle: {
    fontFamily: '"PingFang SC", "Microsoft YaHei", "Segoe UI", system-ui, sans-serif',
    color: '#57534E',
  },
  categoryAxis: {
    axisLine: { lineStyle: { color: '#E7E5E4' } },
    axisTick: { show: false },
    axisLabel: { color: '#A8A29E' },
    splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#A8A29E' },
    splitLine: { lineStyle: { color: '#E7E5E4', type: 'dashed' } },
  },
  legend: {
    textStyle: { color: '#78716C' },
  },
  tooltip: {
    backgroundColor: '#FFFFFF',
    borderColor: '#E7E5E4',
    borderWidth: 1,
    borderRadius: 10,
    padding: [8, 12],
    textStyle: { color: '#44403C' },
    extraCssText: 'box-shadow: 0 4px 16px rgba(28, 25, 23, 0.10); border-radius: 10px;',
  },
  bar: {
    itemStyle: { borderRadius: [4, 4, 0, 0] },
  },
  line: {
    smooth: true,
    symbolSize: 6,
    lineStyle: { width: 2.5 },
  },
  pie: {
    itemStyle: { borderRadius: 4, borderColor: '#FFFFFF', borderWidth: 2 },
  },
};

echarts.registerTheme('warm', warmTheme);

export type ChartOption = echarts.ComposeOption<
  | LineSeriesOption
  | BarSeriesOption
  | PieSeriesOption
  | GridComponentOption
  | TooltipComponentOption
  | LegendComponentOption
>;

type ChartProps = {
  option: ChartOption;
  height?: number;
};

export function Chart({ option, height = 300 }: ChartProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current, 'warm');
    chart.setOption(option);
    const resize = () => chart.resize();
    window.addEventListener('resize', resize);
    return () => {
      window.removeEventListener('resize', resize);
      chart.dispose();
    };
  }, [option]);

  return <div ref={ref} style={{ height }} className="w-full" />;
}
