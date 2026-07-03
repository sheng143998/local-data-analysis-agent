import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopStatusBar } from './TopStatusBar';

export function AppLayout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="min-w-0 flex-1">
        <TopStatusBar />
        <div className="page-enter mx-auto max-w-[1540px] p-4 md:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
