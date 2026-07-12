import { FormEvent, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';

export function RegisterPage() {
  const { user, loading, register } = useAuth();
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  if (!loading && user) return <Navigate to="/app/chat" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirmPassword) return setError('两次输入的密码不一致');
    setError(''); setSubmitting(true);
    try { await register(displayName, email, password); navigate('/app/chat', { replace: true }); }
    catch (caught) { setError(caught instanceof Error ? caught.message : '注册失败，请稍后重试'); }
    finally { setSubmitting(false); }
  }
  return <div className="grid min-h-screen place-items-center bg-slate-950 p-6 text-white"><form onSubmit={submit} className="w-full max-w-lg border border-white/10 bg-white/[0.06] p-8 shadow-2xl" style={{ borderRadius: 8 }}><UserPlus className="mb-5 h-10 w-10 text-cyan-200" /><h1 className="text-3xl font-bold">创建工作区账号</h1><div className="mt-6 grid gap-4"><label className="text-sm text-slate-300">用户名<input value={displayName} onChange={(event) => setDisplayName(event.target.value)} required minLength={1} maxLength={80} className="mt-2 w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-white outline-none" /></label><label className="text-sm text-slate-300">邮箱<input value={email} onChange={(event) => setEmail(event.target.value)} required type="email" autoComplete="email" className="mt-2 w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-white outline-none" /></label><label className="text-sm text-slate-300">密码<input value={password} onChange={(event) => setPassword(event.target.value)} required minLength={12} type="password" autoComplete="new-password" className="mt-2 w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-white outline-none" /></label><label className="text-sm text-slate-300">确认密码<input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required type="password" autoComplete="new-password" className="mt-2 w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-white outline-none" /></label>{error && <p className="text-sm text-rose-300" role="alert">{error}</p>}<button disabled={submitting} className="primary-btn mt-2 w-full bg-cyan-400 text-slate-950 hover:bg-cyan-300 disabled:opacity-60">{submitting ? '创建中...' : '创建账号'}</button></div><p className="mt-5 text-sm text-slate-400">已有账号？ <Link className="text-cyan-200" to="/login">去登录</Link></p></form></div>;
}
