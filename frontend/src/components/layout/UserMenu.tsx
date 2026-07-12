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
  return <div className="relative"><button onClick={() => setOpen((value) => !value)} className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-2.5 py-2 text-sm text-slate-700"><span className="grid h-8 w-8 place-items-center rounded-md bg-slate-950 text-xs font-bold text-cyan-200">{initials}</span><span className="hidden max-w-28 truncate sm:block">{user?.display_name}</span><ChevronDown className="h-4 w-4" /></button>{open && <div className="absolute right-0 z-20 mt-2 w-48 border border-slate-200 bg-white p-2 shadow-cockpit"><Link onClick={() => setOpen(false)} className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100" to="/app/profile"><UserRound className="h-4 w-4" />个人中心</Link><button onClick={signOut} className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-rose-600 hover:bg-rose-50"><LogOut className="h-4 w-4" />退出登录</button></div>}</div>;
}
