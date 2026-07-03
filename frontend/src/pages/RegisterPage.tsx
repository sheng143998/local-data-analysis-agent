import { Link } from 'react-router-dom';
import { CheckCircle2, UserPlus } from 'lucide-react';

export function RegisterPage() {
  const features = ['自然语言提问', '查询结果可追溯', '本地数据库安全只读', '常用问题自动加速'];
  return (
    <div className="grid min-h-screen bg-slate-950 text-white lg:grid-cols-2">
      <section className="flex items-center justify-center p-6">
        <div className="w-full max-w-lg border border-white/10 bg-white/[0.06] p-8 shadow-2xl" style={{ borderRadius: 8 }}>
          <UserPlus className="mb-5 h-10 w-10 text-cyan-200" />
          <h1 className="text-3xl font-bold">创建工作区账号</h1>
          <div className="mt-6 grid gap-4">
            {['用户名', '邮箱', '密码', '确认密码'].map((label) => (
              <label key={label} className="text-sm text-slate-300">
                {label}
                <input className="mt-2 w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-white outline-none focus:border-cyan-300" type={label.includes('密码') ? 'password' : 'text'} />
              </label>
            ))}
            <Link to="/app/chat" className="primary-btn mt-2 w-full bg-cyan-400 text-slate-950 hover:bg-cyan-300">创建账号</Link>
          </div>
          <p className="mt-5 text-sm text-slate-400">
            已有账号？<Link className="text-cyan-200" to="/login">去登录</Link>
          </p>
        </div>
      </section>
      <section className="flex items-center p-8">
        <div className="grid w-full gap-4">
          {features.map((feature) => (
            <div key={feature} className="flex items-center gap-4 border border-cyan-300/20 bg-slate-900/80 p-5" style={{ borderRadius: 8 }}>
              <CheckCircle2 className="h-6 w-6 text-emerald-300" />
              <span className="text-lg font-semibold">{feature}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
