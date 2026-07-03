import { Link } from 'react-router-dom';
import { ArrowRight, Database, GitBranch, LockKeyhole, Mail } from 'lucide-react';

export function LoginPage() {
  return (
    <div className="grid min-h-screen bg-slate-950 text-white lg:grid-cols-[0.92fr_1.08fr]">
      <section className="flex items-center justify-center p-6">
        <div className="w-full max-w-md border border-white/10 bg-white/[0.06] p-8 shadow-2xl backdrop-blur" style={{ borderRadius: 8 }}>
          <div className="mb-8">
            <div className="mb-5 grid h-12 w-12 place-items-center rounded-md border border-cyan-300/40 bg-cyan-300/10">
              <Database className="h-6 w-6 text-cyan-200" />
            </div>
            <h1 className="text-3xl font-bold">本地数据分析 Agent</h1>
            <p className="mt-2 text-slate-300">用自然语言查询你的本地业务数据库</p>
          </div>
          <div className="space-y-4">
            <label className="block text-sm text-slate-300">
              邮箱
              <div className="mt-2 flex items-center gap-2 rounded-md border border-white/10 bg-slate-900 px-3 py-2">
                <Mail className="h-4 w-4 text-slate-500" />
                <input className="w-full bg-transparent text-white outline-none" placeholder="analytics@example.com" />
              </div>
            </label>
            <label className="block text-sm text-slate-300">
              密码
              <div className="mt-2 flex items-center gap-2 rounded-md border border-white/10 bg-slate-900 px-3 py-2">
                <LockKeyhole className="h-4 w-4 text-slate-500" />
                <input className="w-full bg-transparent text-white outline-none" type="password" placeholder="请输入密码" />
              </div>
            </label>
            <Link to="/app/chat" className="primary-btn w-full bg-cyan-400 text-slate-950 hover:bg-cyan-300">
              登录 <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="mt-5 flex justify-between text-sm">
            <button className="text-slate-400 hover:text-white">忘记密码</button>
            <Link className="text-cyan-200 hover:text-cyan-100" to="/register">创建账号</Link>
          </div>
        </div>
      </section>
      <section className="relative hidden overflow-hidden border-l border-white/10 p-10 lg:block">
        <div className="absolute inset-0 opacity-30" style={{ backgroundImage: 'linear-gradient(rgba(34,211,238,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,.14) 1px, transparent 1px)', backgroundSize: '42px 42px' }} />
        <div className="relative mt-16 grid gap-5">
          {['理解问题', '读取数据结构', '生成 SQL', '安全校验', '返回结论'].map((node, index) => (
            <div key={node} className="ml-[calc(var(--i)*36px)] flex w-[420px] items-center gap-4 border border-cyan-300/20 bg-slate-900/80 p-4" style={{ borderRadius: 8, ['--i' as string]: index }}>
              <GitBranch className="h-5 w-5 text-cyan-200" />
              <div>
                <p className="font-semibold">{node}</p>
                <p className="font-mono text-xs text-slate-400">SELECT total_amount FROM orders WHERE status = 'paid'</p>
              </div>
              <span className="ml-auto status-dot" />
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
