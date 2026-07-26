import { FormEvent, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, FileSearch, Loader2, LockKeyhole, Mail, MessageSquareText, ShieldCheck } from 'lucide-react';
import { useAuth } from '../auth/AuthProvider';

const features = [
  { icon: MessageSquareText, title: '自然语言提问', desc: '像聊天一样提出业务问题，马上得到答案和图表' },
  { icon: ShieldCheck, title: '安全只读查询', desc: '只读取数据，不做任何修改，业务数据始终安心' },
  { icon: FileSearch, title: '结果可追溯', desc: '每个结论都能看到数据来自哪里、口径是什么' },
];

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
    <div className="login-backdrop relative grid min-h-screen overflow-hidden text-white lg:grid-cols-[1.05fr_0.95fr]">
      {/* 光斑与光晕层：纯装饰，不响应指针 */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="login-blob login-blob-a -left-40 -top-40" />
        <div className="login-blob login-blob-b right-[-120px] top-1/4" />
        <div className="login-blob login-blob-c bottom-[-140px] left-1/3" />
      </div>

      {/* 品牌侧：产品价值文案，零技术词 */}
      <section className="relative hidden flex-col justify-center p-14 lg:flex">
        <div className="max-w-lg">
          <p className="stagger-item text-sm font-medium tracking-wide text-white/60">本地数据分析助手</p>
          <h2 className="stagger-item stagger-1 mt-4 text-4xl font-bold leading-tight">
            用一句话，
            <br />
            读懂你的业务数据
          </h2>
          <p className="stagger-item stagger-2 mt-4 text-base leading-7 text-white/70">
            不用记表名，不用写公式。把问题说出来，答案、图表和依据一起送到你面前。
          </p>
          <div className="mt-12 space-y-6">
            {features.map((feature, index) => (
              <div key={feature.title} className={`stagger-item stagger-${index + 3} flex items-start gap-4`}>
                <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/15 bg-white/[0.08]">
                  <feature.icon className="h-5 w-5 text-accent-300" />
                </div>
                <div>
                  <p className="font-semibold">{feature.title}</p>
                  <p className="mt-1 text-sm leading-6 text-white/60">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 表单侧：玻璃拟态卡片 + 背后慢旋柔光 */}
      <section className="relative flex items-center justify-center p-6">
        <div className="login-conic left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" aria-hidden="true" />
        <form onSubmit={submit} className="glass-card relative w-full max-w-md p-8">
          <div className="mb-8">
            <h1 className="stagger-item text-3xl font-bold">欢迎回来</h1>
            <p className="stagger-item stagger-1 mt-2 text-white/60">登录后继续你的数据分析。</p>
          </div>
          <div className="space-y-4">
            <label className="stagger-item stagger-2 block text-sm text-white/70">
              邮箱
              <div className="glass-input mt-2">
                <Mail className="h-4 w-4 shrink-0 text-white/40" />
                <input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="email"
                  className="w-full bg-transparent text-white outline-none placeholder:text-white/30"
                  type="email"
                  placeholder="you@example.com"
                />
              </div>
            </label>
            <label className="stagger-item stagger-3 block text-sm text-white/70">
              密码
              <div className="glass-input mt-2">
                <LockKeyhole className="h-4 w-4 shrink-0 text-white/40" />
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  autoComplete="current-password"
                  className="w-full bg-transparent text-white outline-none"
                  type="password"
                />
              </div>
            </label>
            {error && (
              <p key={error} className="shake text-sm text-[#E8A79A]" role="alert">
                {error}
              </p>
            )}
            <button
              disabled={submitting}
              className="primary-btn shimmer-btn stagger-item stagger-4 w-full py-2.5 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> 登录中...
                </>
              ) : (
                <>
                  登录 <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
          <div className="stagger-item stagger-5 mt-6 flex justify-end text-sm">
            <Link className="text-accent-300 transition hover:text-accent-200" to="/register">
              创建账号
            </Link>
          </div>
        </form>
      </section>
    </div>
  );
}
