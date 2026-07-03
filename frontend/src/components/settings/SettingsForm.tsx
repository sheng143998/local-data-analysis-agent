import { Plus } from 'lucide-react';

export function SettingsForm() {
  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <section className="panel p-5">
        <h3 className="text-lg font-bold text-slate-950">模型设置</h3>
        <div className="mt-4 grid gap-4">
          {[
            ['聊天模型', 'Qwen / Llama'],
            ['SQL 生成模型', 'Qwen-Coder'],
            ['Embedding 模型', 'text-embedding-v4'],
            ['向量维度', '1536'],
          ].map(([label, value]) => (
            <label key={label} className="text-sm text-slate-600">
              {label}
              <input className="control mt-2 w-full" defaultValue={value} />
            </label>
          ))}
        </div>
      </section>
      <section className="panel p-5">
        <h3 className="text-lg font-bold text-slate-950">数据库设置</h3>
        <div className="mt-4 grid gap-4">
          <label className="text-sm text-slate-600">PostgreSQL 连接<input className="control mt-2 w-full" defaultValue="postgresql://local:****@127.0.0.1:5432/olist" /></label>
          <label className="flex items-center justify-between rounded-md border border-slate-200 p-3 text-sm">只读模式开关<input type="checkbox" defaultChecked /></label>
          <label className="text-sm text-slate-600">查询超时时间<input className="control mt-2 w-full" defaultValue="30s" /></label>
          <label className="text-sm text-slate-600">最大返回行数<input className="control mt-2 w-full" defaultValue="5000" /></label>
        </div>
      </section>
      <section className="panel p-5">
        <h3 className="text-lg font-bold text-slate-950">安全设置</h3>
        <div className="mt-4 grid gap-3">
          {['只允许 SELECT', '禁止多语句', '表白名单', '自动 LIMIT'].map((item) => (
            <label key={item} className="flex items-center justify-between rounded-md border border-slate-200 p-3 text-sm">
              {item}<input type="checkbox" defaultChecked />
            </label>
          ))}
        </div>
      </section>
      <section className="panel p-5">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-950">API Key 设置</h3>
          <button className="primary-btn"><Plus className="h-4 w-4" /> 新建 Key</button>
        </div>
        <div className="mt-4 space-y-3">
          {[
            ['local-agent-main', '启用', '2026-07-03 11:30'],
            ['etl-service-readonly', '启用', '2026-07-02 21:10'],
            ['legacy-test-key', '停用', '2026-06-20 09:00'],
          ].map(([name, status, last]) => (
            <div key={name} className="flex items-center justify-between rounded-md border border-slate-200 p-3 text-sm">
              <div><p className="font-semibold text-slate-800">{name}</p><p className="text-slate-500">最近使用时间：{last}</p></div>
              <span className={status === '启用' ? 'text-emerald-600' : 'text-slate-400'}>{status}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
