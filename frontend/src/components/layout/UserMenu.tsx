import { Link } from 'react-router-dom';
import { ChevronDown, KeyRound, LogOut, UserRound } from 'lucide-react';

export function UserMenu() {
  return (
    <div className="group relative">
      <button className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-2.5 py-2 text-sm text-slate-700">
        <span className="grid h-8 w-8 place-items-center rounded-md bg-slate-950 text-xs font-bold text-cyan-200">林</span>
        <ChevronDown className="h-4 w-4" />
      </button>
      <div className="invisible absolute right-0 z-20 mt-2 w-44 translate-y-1 border border-slate-200 bg-white p-2 opacity-0 shadow-cockpit transition group-hover:visible group-hover:translate-y-0 group-hover:opacity-100">
        <Link className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100" to="/app/profile">
          <UserRound className="h-4 w-4" /> 个人中心
        </Link>
        <button className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100">
          <KeyRound className="h-4 w-4" /> API Key
        </button>
        <Link className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-rose-600 hover:bg-rose-50" to="/login">
          <LogOut className="h-4 w-4" /> 退出登录
        </Link>
      </div>
    </div>
  );
}
