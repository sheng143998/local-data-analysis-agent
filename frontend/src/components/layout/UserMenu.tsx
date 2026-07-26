import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChevronDown, LogOut, UserRound } from 'lucide-react';
import { useAuth } from '../../auth/AuthProvider';

export function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const initials = user?.display_name.slice(0, 1).toUpperCase() || '?';
  async function signOut() { await logout(); navigate('/login', { replace: true }); }
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((value) => !value)}
        className="flex items-center gap-2 rounded-xl border border-stone-200 bg-white px-2 py-1.5 text-sm text-stone-700 transition duration-150 hover:border-stone-300"
      >
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent-100 text-xs font-bold text-accent-700">{initials}</span>
        <span className="hidden max-w-28 truncate sm:block">{user?.display_name}</span>
        <ChevronDown className="h-4 w-4 text-stone-400" />
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-48 rounded-xl border border-stone-200 bg-white p-2 shadow-lift">
          <Link
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-stone-700 transition hover:bg-stone-50"
            to="/app/profile"
          >
            <UserRound className="h-4 w-4" />个人中心
          </Link>
          <button
            onClick={signOut}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-danger transition hover:bg-danger-soft"
          >
            <LogOut className="h-4 w-4" />退出登录
          </button>
        </div>
      )}
    </div>
  );
}
