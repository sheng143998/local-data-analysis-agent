import type { ColumnDef } from '@tanstack/react-table';
import { Chart } from '../common/Chart';
import { DataTable } from '../common/DataTable';
import { failureRows, pathShare, salesTrend } from '../../data/mock';

type FailureRow = { question: string; reason: string; sql: string; status: string };
const failureData = failureRows.map(([question, reason, sql, status]) => ({ question, reason, sql, status }));

const columns: ColumnDef<FailureRow>[] = [
  { accessorKey: 'question', header: '用户问题' },
  { accessorKey: 'reason', header: '失败原因' },
  { accessorKey: 'sql', header: '错误 SQL' },
  { accessorKey: 'status', header: '修复状态' },
];

export function EvaluationDashboard() {
  const stats = [
    ['SQL 生成成功率', '96.8%'],
    ['SQL 执行成功率', '94.2%'],
    ['记忆命中率', '68.4%'],
    ['复用成功率', '91.5%'],
    ['平均延迟', '912ms'],
    ['平均模型调用次数', '1.8'],
  ];
  return (
    <div className="grid gap-5">
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        {stats.map(([label, value]) => (
          <div key={label} className="panel p-4">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-5 xl:grid-cols-3">
        <section className="panel p-5 xl:col-span-2">
          <h3 className="text-lg font-bold text-slate-950">成功率趋势</h3>
          <Chart
            option={{
              tooltip: { trigger: 'axis' },
              grid: { left: 38, right: 18, top: 34, bottom: 34 },
              xAxis: { type: 'category', data: salesTrend.slice(-14).map((item) => item.date.slice(5)) },
              yAxis: { type: 'value', min: 80, max: 100 },
              series: [{ type: 'line', smooth: true, data: [91, 92, 93, 92, 94, 95, 94, 96, 95, 97, 96, 96.4, 96.8, 97.2], lineStyle: { color: '#10b981', width: 3 } }],
            }}
          />
        </section>
        <section className="panel p-5">
          <h3 className="text-lg font-bold text-slate-950">三种路径占比</h3>
          <Chart
            option={{
              tooltip: { trigger: 'item' },
              series: [{ type: 'pie', radius: ['48%', '72%'], data: pathShare, color: ['#10b981', '#0891b2', '#f59e0b'] }],
            }}
          />
        </section>
      </div>
      <section className="panel overflow-hidden">
        <div className="border-b border-slate-200 p-5">
          <h3 className="text-lg font-bold text-slate-950">失败案例列表</h3>
        </div>
        <DataTable data={failureData} columns={columns} />
      </section>
    </div>
  );
}
