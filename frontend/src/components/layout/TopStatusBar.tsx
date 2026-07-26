import { UserMenu } from './UserMenu';

export function TopStatusBar() {
  return (
    <header className="sticky top-0 z-10 border-b border-stone-200/70 bg-paper/85 px-4 py-2 backdrop-blur md:px-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2 text-sm">
          <span className="text-stone-400">工作区</span>
          <span className="text-stone-300">/</span>
          <span className="truncate font-medium text-stone-800">本地电商分析</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden items-center gap-2 text-xs text-stone-500 sm:flex">
            <span className="status-dot" /> 服务正常
          </span>
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
