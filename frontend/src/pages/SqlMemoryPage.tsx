import { PageHeader } from '../components/common/PageHeader';
import { SqlMemoryTable } from '../components/sql-memory/SqlMemoryTable';

export function SqlMemoryPage() {
  return (
    <>
      <PageHeader title="SQL 记忆" description="开发者与高级用户用于管理历史成功 SQL 模板、命中率和复用路径。" />
      <div className="mb-5 grid gap-4 md:grid-cols-4">
        {[
          ['记忆总数', '218'],
          ['平均命中率', '68.4%'],
          ['fast_path 占比', '48%'],
          ['rewrite_path 占比', '34%'],
        ].map(([label, value]) => (
          <div key={label} className="panel p-4">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
          </div>
        ))}
      </div>
      <SqlMemoryTable />
    </>
  );
}
