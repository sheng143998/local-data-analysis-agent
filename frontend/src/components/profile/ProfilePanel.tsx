export function ProfilePanel() {
  return (
    <div className="grid gap-5 xl:grid-cols-[380px_1fr]">
      <section className="panel p-6">
        <div className="grid h-24 w-24 place-items-center rounded-md bg-slate-950 text-3xl font-bold text-cyan-200">林</div>
        <h3 className="mt-5 text-xl font-bold text-slate-950">林知远</h3>
        <p className="text-sm text-slate-500">analytics@example.com</p>
        <div className="mt-5 space-y-3 text-sm">
          <p><span className="text-slate-500">角色：</span>数据分析负责人</p>
          <p><span className="text-slate-500">所属工作区：</span>本地电商分析</p>
        </div>
        <div className="mt-6 grid gap-3">
          <button className="secondary-btn">修改资料</button>
          <button className="secondary-btn">修改密码</button>
          <button className="primary-btn bg-rose-600 hover:bg-rose-500">退出登录</button>
        </div>
      </section>
      <section className="panel p-6">
        <h3 className="text-lg font-bold text-slate-950">使用统计</h3>
        <div className="mt-5 grid gap-4 md:grid-cols-4">
          {[
            ['今日查询次数', '42'],
            ['本月查询次数', '1,286'],
            ['常用数据表', 'orders'],
            ['常用指标', '销售额'],
          ].map(([label, value]) => (
            <div key={label} className="sub-panel p-4">
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
