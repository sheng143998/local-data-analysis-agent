import { Copy, ShieldCheck } from 'lucide-react';
import { finalSql } from '../../data/mock';

export function SqlPanel() {
  return (
    <section className="panel overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 p-5">
        <div>
          <h3 className="text-lg font-bold text-slate-950">最终执行 SQL</h3>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="rounded bg-slate-100 px-2 py-1 font-semibold text-slate-700">PostgreSQL</span>
            <span className="rounded bg-emerald-50 px-2 py-1 font-semibold text-emerald-700">
              <ShieldCheck className="mr-1 inline h-3.5 w-3.5" /> 已通过校验
            </span>
            <span className="rounded bg-cyan-50 px-2 py-1 font-semibold text-cyan-700">只读查询</span>
          </div>
        </div>
        <button className="secondary-btn">
          <Copy className="h-4 w-4" /> 复制 SQL
        </button>
      </div>
      <pre className="code-block m-5 animate-[page-in_520ms_ease]">
        <code>{finalSql}</code>
      </pre>
    </section>
  );
}
