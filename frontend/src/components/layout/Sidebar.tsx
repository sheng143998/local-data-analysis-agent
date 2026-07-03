import { NavLink } from 'react-router-dom';
import { BookOpenText, Database, Gauge, MessageSquareText, Settings, UserRound } from 'lucide-react';

const navItems = [
  { to: '/app/chat', label: '数据问答', icon: MessageSquareText },
  { to: '/app/data-sources', label: '数据源', icon: Database },
  { to: '/app/metrics', label: '指标口径', icon: BookOpenText },
  { to: '/app/profile', label: '个人中心', icon: UserRound },
  { to: '/app/settings', label: '系统设置', icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-72 shrink-0 flex-col bg-slate-950 text-white shadow-2xl lg:flex">
      <div className="border-b border-white/10 p-6">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-md border border-cyan-300/40 bg-cyan-300/10">
            <Gauge className="h-5 w-5 text-cyan-200" />
          </div>
          <div>
            <p className="text-sm text-slate-400">数据分析助手</p>
            <h1 className="text-lg font-semibold">本地数据分析 Agent</h1>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              [
                'group flex items-center gap-3 rounded-md px-4 py-3 text-sm font-medium transition',
                isActive
                  ? 'bg-cyan-300/12 text-cyan-100 shadow-line'
                  : 'text-slate-300 hover:bg-white/6 hover:text-white',
              ].join(' ')
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 p-5 text-xs leading-6 text-slate-400">
        <p className="font-semibold text-slate-300">面向业务分析</p>
        <p className="mt-1">用自然语言提问，维护指标口径，沉淀团队统一分析标准。</p>
      </div>
    </aside>
  );
}
