import { FormEvent, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, Database, LockKeyhole, Mail } from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';

export function LoginPage() {
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const destination = (location.state as { from?: string } | null)?.from ?? '/app/chat';

  if (!loading && user) return <Navigate to={destination} replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(destination, { replace: true });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '登录失败，请稍后重试');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-slate-950 text-white lg:grid-cols-[0.92fr_1.08fr]">
      <section className="flex items-center justify-center p-6">
        <form onSubmit={submit} className="w-full max-w-md border border-white/10 bg-white/[0.06] p-8 shadow-2xl backdrop-blur" style={{ borderRadius: 8 }}>
          <div className="mb-8"><div className="mb-5 grid h-12 w-12 place-items-center rounded-md border border-cyan-300/40 bg-cyan-300/10"><Database className="h-6 w-6 text-cyan-200" /></div><h1 className="text-3xl font-bold">本地数据分析 Agent</h1><p className="mt-2 text-slate-300">使用账号访问本地业务数据分析工作区。</p></div>
          <div className="space-y-4">
            <label className="block text-sm text-slate-300">邮箱<div className="mt-2 flex items-center gap-2 rounded-md border border-white/10 bg-slate-900 px-3 py-2"><Mail className="h-4 w-4 text-slate-500" /><input value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" className="w-full bg-transparent text-white outline-none" type="email" placeholder="analytics@example.com" /></div></label>
            <label className="block text-sm text-slate-300">密码<div className="mt-2 flex items-center gap-2 rounded-md border border-white/10 bg-slate-900 px-3 py-2"><LockKeyhole className="h-4 w-4 text-slate-500" /><input value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" className="w-full bg-transparent text-white outline-none" type="password" /></div></label>
            {error && <p className="text-sm text-rose-300" role="alert">{error}</p>}
            <button disabled={submitting} className="primary-btn w-full bg-cyan-400 text-slate-950 hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60">{submitting ? '登录中...' : '登录'} <ArrowRight className="h-4 w-4" /></button>
          </div>
          <div className="mt-5 flex justify-end text-sm"><Link className="text-cyan-200 hover:text-cyan-100" to="/register">创建账号</Link></div>
        </form>
      </section>
      <section className="hidden border-l border-white/10 p-10 lg:block"><div className="mt-20 max-w-lg border border-cyan-300/20 bg-slate-900/80 p-7" style={{ borderRadius: 8 }}><h2 className="text-xl font-semibold">数据分析工作区</h2><p className="mt-3 text-slate-300">登录后可进行受保护的数据问答，并按角色管理指标和开发者调试能力。</p></div></section>
    </div>
  );
}
