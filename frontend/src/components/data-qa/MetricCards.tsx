import { TrendingDown, TrendingUp } from 'lucide-react';
import { formatNumericText } from '../../lib/format';
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
              <p className="text-sm text-stone-500">{card.label}</p>
              <p className="mt-2 text-2xl font-bold text-stone-900">{formatNumericText(card.value)}</p>
            </div>
            {card.delta.startsWith('-') ? (
              <TrendingDown className="h-5 w-5 text-success" />
            ) : (
              <TrendingUp className="h-5 w-5 text-success" />
            )}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs">
            <span className="font-semibold text-success">{card.delta}</span>
            <span className="text-stone-500">{card.hint}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
