import { MetricCards } from './MetricCards';
import type { AnalysisMetric } from '../../types/analysis';

type AnswerPanelProps = {
  summary?: string;
  metrics?: AnalysisMetric[];
};

export function AnswerPanel({ summary, metrics = [] }: AnswerPanelProps) {
  return (
    <section className="panel p-5">
      <h3 className="text-lg font-bold text-slate-950">分析总结</h3>
      <p className="mt-3 text-sm leading-7 text-slate-600">
        {summary ?? '暂无分析结果。'}
      </p>
      <div className="mt-5">
        <MetricCards metrics={metrics} />
      </div>
    </section>
  );
}
