import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

const PATH_LABELS: Record<string, string> = {
  cold_path: '全新分析',
  rewrite_path: '参考历史经验',
  fast_path: '复用已验证查询',
};

/** 开发者信息：默认折叠，仅供排查；普通视图不展示内部枚举与模型信息。 */
export function DeveloperTracePanel() {
  const [open, setOpen] = useState(false);
  const rows = [
    ['分析方式', PATH_LABELS.rewrite_path],
    ['工具调用次数', '4'],
    ['模型调用次数', '2'],
    ['历史经验候选数', '12'],
    ['总耗时', '912ms'],
  ];
  return (
    <section className="panel">
      <button className="flex w-full items-center justify-between p-5 text-left" onClick={() => setOpen((value) => !value)}>
        <div>
          <h3 className="text-lg font-bold text-stone-900">开发者信息</h3>
          <p className="text-sm text-stone-500">默认折叠，仅在排查问题时需要展开</p>
        </div>
        <ChevronDown className={`h-5 w-5 text-stone-400 transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open ? (
        <div className="grid gap-3 border-t border-stone-200 p-5 md:grid-cols-5">
          {rows.map(([label, value]) => (
            <div key={label} className="sub-panel p-3">
              <p className="text-xs text-stone-500">{label}</p>
              <p className="nums mt-1 text-sm font-semibold text-stone-900">{value}</p>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
