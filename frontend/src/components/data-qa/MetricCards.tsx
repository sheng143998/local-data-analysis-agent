import { TrendingDown, TrendingUp } from 'lucide-react';
import { metricCards } from '../../data/mock';

export function MetricCards() {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {metricCards.map((card, index) => (
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
          <svg className="mt-3 h-9 w-full" viewBox="0 0 120 36" preserveAspectRatio="none">
            <path
              d={`M0 ${24 - index * 2} C 20 8, 28 28, 46 14 S 74 10, 90 18 S 108 12, 120 ${8 + index}`}
              fill="none"
              stroke={index === 2 ? '#f59e0b' : '#10b981'}
              strokeWidth="3"
              strokeLinecap="round"
              strokeDasharray="420"
              style={{ animation: 'draw-line 1.2s ease forwards' }}
            />
          </svg>
        </div>
      ))}
    </div>
  );
}
