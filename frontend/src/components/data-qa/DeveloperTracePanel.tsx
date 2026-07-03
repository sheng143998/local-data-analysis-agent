import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export function DeveloperTracePanel() {
  const [open, setOpen] = useState(false);
  const rows = [
    ['执行路径', 'rewrite_path'],
    ['工具调用次数', '4'],
    ['模型调用次数', '2'],
    ['SQL 记忆候选数', '12'],
    ['总耗时', '912ms'],
  ];
  return (
    <section className="panel">
      <button className="flex w-full items-center justify-between p-5 text-left" onClick={() => setOpen((value) => !value)}>
        <div>
          <h3 className="text-lg font-bold text-slate-950">开发者追踪</h3>
          <p className="text-sm text-slate-500">默认折叠，供高级用户排查执行路径</p>
        </div>
        <ChevronDown className={`h-5 w-5 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open ? (
        <div className="grid gap-3 border-t border-slate-200 p-5 md:grid-cols-5">
          {rows.map(([label, value]) => (
            <div key={label} className="sub-panel p-3">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="mt-1 font-mono text-sm font-semibold text-slate-900">{value}</p>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
