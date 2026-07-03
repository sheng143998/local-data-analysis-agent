import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

type ChartProps = {
  option: echarts.EChartsOption;
  height?: number;
};

export function Chart({ option, height = 300 }: ChartProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
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
