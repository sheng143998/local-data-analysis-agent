import { LockKeyhole, Shield, TimerReset } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export function TrustPanel() {
  const items: Array<[string, string, LucideIcon]> = [
    ['只读数据库', '所有查询强制 SELECT 校验', Shield],
    ['本地执行', 'PostgreSQL 连接不离开工作区', LockKeyhole],
    ['可追溯结果', 'SQL、数据源、口径完整记录', TimerReset],
  ];

  return (
    <section className="grid gap-4 md:grid-cols-3">
      {items.map(([title, desc, Icon]) => (
        <div key={String(title)} className="sub-panel p-4">
          <Icon className="h-5 w-5 text-cyan-600" />
          <p className="mt-3 font-semibold text-slate-950">{title}</p>
          <p className="mt-1 text-sm text-slate-500">{desc}</p>
        </div>
      ))}
    </section>
  );
}
