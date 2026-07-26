import { NavLink } from 'react-router-dom';
import { BookOpenText, Database, MessageSquareText, Settings, UserRound } from 'lucide-react';

const navItems = [
  { to: '/app/chat', label: '数据问答', icon: MessageSquareText },
  { to: '/app/data-sources', label: '数据源', icon: Database },
  { to: '/app/metrics', label: '指标口径', icon: BookOpenText },
  { to: '/app/profile', label: '个人中心', icon: UserRound },
  { to: '/app/settings', label: '系统设置', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-64 shrink-0 flex-col border-r border-stone-200 bg-white lg:flex">
      <div className="p-6">
        <p className="text-lg font-bold tracking-tight text-stone-900">本地数据分析助手</p>
        <p className="mt-1 text-xs text-stone-400">用日常语言，读懂业务数据</p>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              [
                'group relative flex items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium transition duration-150',
                isActive
                  ? 'bg-accent-50 text-accent-700'
                  : 'text-stone-600 hover:bg-stone-50 hover:text-stone-900',
              ].join(' ')
            }
          >
            {({ isActive }) => (
              <>
                {isActive ? (
                  <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-full bg-accent" aria-hidden="true" />
                ) : null}
                <item.icon className={['h-4 w-4', isActive ? 'text-accent' : 'text-stone-500'].join(' ')} />
                {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-stone-100 p-5 text-xs leading-6 text-stone-400">
        <p className="font-semibold text-stone-500">面向业务分析</p>
        <p className="mt-1">用自然语言提问，维护指标口径，沉淀团队统一分析标准。</p>
      </div>
    </aside>
  );
}
