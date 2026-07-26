import { useState } from 'react';
import { AgentPipeline } from '../data-qa/AgentPipeline';
import { DeveloperTracePanel } from '../data-qa/DeveloperTracePanel';
import { SourcePanel } from '../data-qa/SourcePanel';
import { SqlPanel } from '../data-qa/SqlPanel';
import { TrustPanel } from '../data-qa/TrustPanel';
import type { ChatItem } from '../../lib/chat';

type DetailTab = 'sql' | 'trace' | 'source';

type AnalysisDetailsProps = Pick<ChatItem, 'sql' | 'steps'>;

/**
 * 渐进式披露：答案与图表默认展示在外部，查询语句 / 分析过程 / 数据来源
 * 放在此折叠区域内，通过小标签页按需展开（默认全部收起，普通视图零术语）。
 */
export function AnalysisDetails({ sql, steps }: AnalysisDetailsProps) {
  const [activeTab, setActiveTab] = useState<DetailTab | null>(null);
  const tabs: Array<{ key: DetailTab; label: string; available: boolean }> = [
    { key: 'sql', label: '查询语句', available: Boolean(sql) },
    { key: 'trace', label: '分析过程', available: true },
    { key: 'source', label: '数据来源', available: true },
  ];
  const visibleTabs = tabs.filter((tab) => tab.available);
  if (!visibleTabs.length) return null;

  const toggleTab = (tab: DetailTab) => setActiveTab((current) => (current === tab ? null : tab));

  return (
    <section className="overflow-hidden rounded-2xl border border-stone-200 bg-stone-50/70">
      <div className="flex flex-wrap items-center gap-2 px-3 py-2">
        <span className="text-xs text-stone-500">查看分析详情</span>
        {visibleTabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => toggleTab(tab.key)}
            aria-expanded={activeTab === tab.key}
            className={[
              'rounded-full px-3 py-1 text-xs font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-accent text-white'
                : 'border border-stone-200 bg-white text-stone-600 hover:border-accent-300 hover:text-accent-700',
            ].join(' ')}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab ? (
        <div className="max-h-[min(62vh,720px)] space-y-4 overflow-y-auto border-t border-stone-200 p-4">
          {activeTab === 'sql' && sql ? <SqlPanel sql={sql} compact title="本次使用的查询语句" /> : null}
          {activeTab === 'trace' ? (
            <>
              <AgentPipeline running={false} steps={steps ?? []} />
              <DeveloperTracePanel />
            </>
          ) : null}
          {activeTab === 'source' ? (
            <>
              <SourcePanel />
              <TrustPanel />
            </>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
