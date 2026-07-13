import { TrendingDown, TrendingUp } from 'lucide-react';
import type { AnalysisMetric } from '../../types/analysis';

type MetricCardsProps = {
  metrics: AnalysisMetric[];
};

export function MetricCards({ metrics }: MetricCardsProps) {
  if (!metrics.length) return null;

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {metrics.map((card) => (
        <div key={card.label} className="sub-panel overflow-hidden p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500">{card.label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{card.value}</p>
            </div>
            {card.delta.startsWith('-') ? (
              <TrendingDown className="h-5 w-5 text-emerald-500" />
            ) : (
              <TrendingUp className="h-5 w-5 text-emerald-500" />
            )}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs">
            <span className="font-semibold text-emerald-600">{card.delta}</span>
            <span className="text-slate-500">{card.hint}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
