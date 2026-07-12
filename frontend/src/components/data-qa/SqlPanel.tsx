import { Check, ChevronsDownUp, ChevronsUpDown, Copy, Database, ShieldCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import { finalSql } from '../../data/mock';

type SqlPanelProps = {
  sql?: string;
  compact?: boolean;
  title?: string;
};

const LONG_SQL_THRESHOLD = 520;

export function SqlPanel({ sql = finalSql, compact = false, title = 'SQL' }: SqlPanelProps) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const shouldCollapse = sql.length > LONG_SQL_THRESHOLD || sql.split('\n').length > 12;
  const isCollapsed = shouldCollapse && !expanded;

  const lineCount = useMemo(() => sql.split('\n').filter(Boolean).length || 1, [sql]);

  const copySql = async () => {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className={compact ? 'sub-panel overflow-hidden bg-white' : 'panel overflow-hidden'}>
      <div
        className={
          compact
            ? 'flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3'
            : 'flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-5'
        }
      >
        <div>
          <h3 className={compact ? 'flex items-center gap-2 text-sm font-bold text-slate-950' : 'text-lg font-bold text-slate-950'}>
            {compact ? <Database className="h-4 w-4 text-cyan-600" /> : null}
            {title}
          </h3>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="rounded bg-slate-100 px-2 py-1 font-semibold text-slate-700">PostgreSQL</span>
            <span className="rounded bg-emerald-50 px-2 py-1 font-semibold text-emerald-700">
              <ShieldCheck className="mr-1 inline h-3.5 w-3.5" /> 只读校验
            </span>
            <span className="rounded bg-cyan-50 px-2 py-1 font-semibold text-cyan-700">{lineCount} 行</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {shouldCollapse ? (
            <button
              type="button"
              onClick={() => setExpanded((value) => !value)}
              className="secondary-btn px-3"
              aria-expanded={expanded}
            >
              {expanded ? <ChevronsDownUp className="h-4 w-4" /> : <ChevronsUpDown className="h-4 w-4" />}
              {expanded ? '收起' : '展开'}
            </button>
          ) : null}
          <button type="button" onClick={copySql} className="secondary-btn px-3">
            {copied ? <Check className="h-4 w-4 text-emerald-600" /> : <Copy className="h-4 w-4" />}
            {copied ? '已复制' : '复制'}
          </button>
        </div>
      </div>
      <div className={compact ? 'p-4' : 'p-5'}>
        <pre
          className={[
            'code-block sql-code-block animate-[page-in_520ms_ease]',
            isCollapsed ? 'max-h-56' : 'max-h-[32rem]',
          ].join(' ')}
        >
          <code>{sql}</code>
        </pre>
        {isCollapsed ? (
          <div className="mt-2 text-xs text-slate-500">SQL 较长，已折叠预览。可展开查看完整内容，或直接复制完整 SQL。</div>
        ) : null}
      </div>
    </section>
  );
}
