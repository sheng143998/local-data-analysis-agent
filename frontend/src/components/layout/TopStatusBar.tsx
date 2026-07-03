import { Bell, Search } from 'lucide-react';
import { UserMenu } from './UserMenu';

export function TopStatusBar() {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-[#e8eef3]/88 px-4 py-3 backdrop-blur md:px-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs text-slate-500">当前工作区</p>
          <div className="text-sm font-semibold text-slate-900">本地电商分析</div>
        </div>
        <div className="flex min-w-0 flex-1 justify-center px-4">
          <div className="hidden w-full max-w-xl items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 md:flex">
            <Search className="h-4 w-4" />
            搜索会话、指标或数据表
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="grid h-10 w-10 place-items-center rounded-md border border-slate-200 bg-white text-slate-600">
            <Bell className="h-4 w-4" />
          </button>
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
