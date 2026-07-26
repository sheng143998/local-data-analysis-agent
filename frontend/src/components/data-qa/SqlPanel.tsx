import { Check, ChevronsDownUp, ChevronsUpDown, Copy, Database, ShieldCheck } from 'lucide-react';
import { Fragment, useMemo, useState } from 'react';

type SqlPanelProps = {
  sql: string;
  compact?: boolean;
  title?: string;
};

const LONG_SQL_THRESHOLD = 520;

const SQL_KEYWORDS =
  /\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT|OFFSET|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|ON|AS|AND|OR|NOT|IN|IS|NULL|CASE|WHEN|THEN|ELSE|END|WITH|UNION|ALL|DISTINCT|COUNT|SUM|AVG|MIN|MAX|COALESCE|NULLIF|ROUND|CAST|BETWEEN|LIKE|EXISTS|DATE_TRUNC|INTERVAL|DESC|ASC)\b/gi;

/** 零依赖的关键字高亮：只做展示层着色，不改动 SQL 文本本身。 */
function highlightSql(sql: string) {
  const segments: Array<{ text: string; keyword: boolean }> = [];
  let lastIndex = 0;
  for (const match of sql.matchAll(SQL_KEYWORDS)) {
    const index = match.index ?? 0;
    if (index > lastIndex) segments.push({ text: sql.slice(lastIndex, index), keyword: false });
    segments.push({ text: match[0], keyword: true });
    lastIndex = index + match[0].length;
  }
  if (lastIndex < sql.length) segments.push({ text: sql.slice(lastIndex), keyword: false });
  return segments;
}

export function SqlPanel({ sql, compact = false, title = '查询语句' }: SqlPanelProps) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const shouldCollapse = sql.length > LONG_SQL_THRESHOLD || sql.split('\n').length > 12;
  const isCollapsed = shouldCollapse && !expanded;

  const lineCount = useMemo(() => sql.split('\n').filter(Boolean).length || 1, [sql]);
  const segments = useMemo(() => highlightSql(sql), [sql]);

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
            ? 'flex flex-wrap items-center justify-between gap-3 border-b border-stone-200 px-4 py-3'
            : 'flex flex-wrap items-center justify-between gap-3 border-b border-stone-200 p-5'
        }
      >
        <div>
          <h3 className={compact ? 'flex items-center gap-2 text-sm font-bold text-stone-900' : 'text-lg font-bold text-stone-900'}>
            {compact ? <Database className="h-4 w-4 text-accent" /> : null}
            {title}
          </h3>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-stone-100 px-2.5 py-1 font-medium text-stone-600">本地数据库</span>
            <span className="rounded-full bg-success-soft px-2.5 py-1 font-medium text-success">
              <ShieldCheck className="mr-1 inline h-3.5 w-3.5" /> 只读，不改动数据
            </span>
            <span className="nums rounded-full bg-stone-100 px-2.5 py-1 font-medium text-stone-600">{lineCount} 行</span>
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
            {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
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
          <code>
            {segments.map((segment, index) => (
              <Fragment key={index}>
                {segment.keyword ? <span className="sql-keyword">{segment.text}</span> : segment.text}
              </Fragment>
            ))}
          </code>
        </pre>
        {isCollapsed ? (
          <div className="mt-2 text-xs text-stone-500">语句较长已折叠，可展开查看完整内容，或直接复制。</div>
        ) : null}
      </div>
    </section>
  );
}
