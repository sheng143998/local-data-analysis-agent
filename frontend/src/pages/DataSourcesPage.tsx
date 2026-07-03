import { Database, ShieldCheck } from 'lucide-react';
import { PageHeader } from '../components/common/PageHeader';
import { DataSourceTable } from '../components/data-sources/DataSourceTable';

export function DataSourcesPage() {
  return (
    <>
      <PageHeader title="数据源" description="管理本地 PostgreSQL 连接、公开数据集和合成增强数据表。" />
      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <div className="panel p-5">
          <Database className="h-6 w-6 text-cyan-600" />
          <p className="mt-3 text-sm text-slate-500">数据库连接状态</p>
          <p className="text-xl font-bold text-slate-950">PostgreSQL 已连接</p>
        </div>
        <div className="panel p-5 md:col-span-2">
          <ShieldCheck className="h-6 w-6 text-emerald-600" />
          <p className="mt-3 text-sm text-slate-500">连接信息</p>
          <p className="font-mono text-sm text-slate-700">host=127.0.0.1 port=5432 db=olist user=local_agent password=******</p>
          <p className="mt-2 text-sm text-slate-500">数据集：Olist 巴西电商公开数据集、合成增强数据</p>
        </div>
      </div>
      <DataSourceTable />
    </>
  );
}
