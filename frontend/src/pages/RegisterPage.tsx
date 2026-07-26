import { FormEvent, useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { Loader2, UserPlus } from 'lucide-react';
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

  const fields = [
    { key: 'name', label: '用户名', node: (
      <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} required minLength={1} maxLength={80} className="w-full bg-transparent text-white outline-none" />
    ) },
    { key: 'email', label: '邮箱', node: (
      <input value={email} onChange={(event) => setEmail(event.target.value)} required type="email" autoComplete="email" className="w-full bg-transparent text-white outline-none" />
    ) },
    { key: 'password', label: '密码', node: (
      <input value={password} onChange={(event) => setPassword(event.target.value)} required minLength={12} type="password" autoComplete="new-password" className="w-full bg-transparent text-white outline-none" />
    ) },
    { key: 'confirm', label: '确认密码', node: (
      <input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} required type="password" autoComplete="new-password" className="w-full bg-transparent text-white outline-none" />
    ) },
  ];

  return (
    <div className="login-backdrop relative grid min-h-screen place-items-center overflow-hidden p-6 text-white">
      {/* 光斑与光晕层：纯装饰，不响应指针 */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="login-blob login-blob-a -left-48 -top-48" />
        <div className="login-blob login-blob-b right-[-140px] top-1/3" />
        <div className="login-blob login-blob-c bottom-[-160px] left-1/4" />
      </div>
      <div className="login-conic left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" aria-hidden="true" />

      <form onSubmit={submit} className="glass-card relative w-full max-w-lg p-8">
        <div className="stagger-item mb-2 grid h-12 w-12 place-items-center rounded-2xl border border-white/15 bg-white/[0.08]">
          <UserPlus className="h-6 w-6 text-accent-300" />
        </div>
        <h1 className="stagger-item stagger-1 mt-4 text-3xl font-bold">创建你的账号</h1>
        <p className="stagger-item stagger-2 mt-2 text-white/60">注册后即可用日常语言探索业务数据。</p>
        <div className="mt-6 grid gap-4">
          {fields.map((field, index) => (
            <label key={field.key} className={`stagger-item stagger-${index + 3} block text-sm text-white/70`}>
              {field.label}
              <div className="glass-input mt-2">{field.node}</div>
            </label>
          ))}
          {error && (
            <p key={error} className="shake text-sm text-[#E8A79A]" role="alert">
              {error}
            </p>
          )}
          <button
            disabled={submitting}
            className="primary-btn shimmer-btn stagger-item stagger-7 mt-2 w-full py-2.5 disabled:opacity-60"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> 创建中...
              </>
            ) : (
              '创建账号'
            )}
          </button>
        </div>
        <p className="stagger-item stagger-8 mt-6 text-sm text-white/50">
          已有账号？{' '}
          <Link className="text-accent-300 transition hover:text-accent-200" to="/login">
            去登录
          </Link>
        </p>
      </form>
    </div>
  );
}
