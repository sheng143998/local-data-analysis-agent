import { LockKeyhole, Shield, TimerReset } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

/** 数据保障：面向普通用户的表述，不出现校验器/白名单等实现术语。 */
export function TrustPanel() {
  const items: Array<[string, string, LucideIcon]> = [
    ['只读不改动', '助手只读取数据，不会修改或删除任何记录', Shield],
    ['数据不出本机', '所有分析都在你的本地工作区内完成', LockKeyhole],
    ['每一步可追溯', '每个答案都保留了查询语句与数据来源', TimerReset],
  ];

  return (
    <section className="grid gap-4 md:grid-cols-3">
      {items.map(([title, desc, Icon]) => (
        <div key={String(title)} className="sub-panel p-4">
          <Icon className="h-5 w-5 text-accent" />
          <p className="mt-3 font-semibold text-stone-900">{title}</p>
          <p className="mt-1 text-sm text-stone-500">{desc}</p>
        </div>
      ))}
    </section>
  );
}
