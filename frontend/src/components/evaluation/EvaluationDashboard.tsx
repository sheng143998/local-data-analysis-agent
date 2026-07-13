import { useEffect, useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import { Chart } from '../common/Chart';
import { DataTable } from '../common/DataTable';
import { listRuns } from '../../api/developerClient';
import type { QueryRunRecord } from '../../types/developer';

function percent(numerator: number, denominator: number) {
  return denominator ? `${((numerator / denominator) * 100).toFixed(1)}%` : '-';
}

export function EvaluationDashboard() {
  const [runs, setRuns] = useState<QueryRunRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    listRuns()
      .then((items) => active && setRuns(items))
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : '读取运行摘要失败'))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const stats = useMemo(() => {
    const successful = runs.filter((run) => run.execution_status === 'success');
    const allowed = runs.filter((run) => run.guard_status === 'allowed');
    const memoryHits = runs.filter((run) => run.memory_hit);
    const averageLatency = runs.length ? Math.round(runs.reduce((total, run) => total + run.latency_ms, 0) / runs.length) : 0;
    return [
      ['最近运行数', String(runs.length)],
      ['执行成功率', percent(successful.length, runs.length)],
      ['Guard 通过率', percent(allowed.length, runs.length)],
      ['记忆命中率', percent(memoryHits.length, runs.length)],
      ['平均延迟', runs.length ? `${averageLatency}ms` : '-'],
    ];
  }, [runs]);
  const trend = useMemo(() => {
    const days = new Map<string, { total: number; success: number }>();
    [...runs].reverse().forEach((run) => {
      const day = new Date(run.created_at).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
      const value = days.get(day) ?? { total: 0, success: 0 };
      value.total += 1;
      if (run.execution_status === 'success') value.success += 1;
      days.set(day, value);
    });
    return [...days.entries()].slice(-14).map(([day, value]) => ({ day, value: Number((value.success / value.total * 100).toFixed(1)) }));
  }, [runs]);
  const failedRuns = useMemo(() => runs.filter((run) => run.execution_status !== 'success' || run.guard_status !== 'allowed'), [runs]);
  const columns = useMemo<ColumnDef<QueryRunRecord>[]>(() => [
    { accessorKey: 'user_question', header: '用户问题' },
    { accessorKey: 'guard_status', header: 'Guard 状态' },
    { accessorKey: 'execution_status', header: '执行状态' },
    { accessorKey: 'error_message', header: '失败原因', cell: ({ getValue }) => getValue<string | null>() ?? '-' },
  ], []);

  if (loading) return <section className="panel p-5 text-sm text-slate-500">正在读取真实运行摘要...</section>;
  if (error) return <section className="panel p-5 text-sm text-rose-700">{error}</section>;
  if (!runs.length) return <section className="panel p-5 text-sm text-slate-500">暂无可用于展示的真实运行记录。正式离线评测报告请通过评测工件查看。</section>;

  return (
    <div className="grid gap-5">
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
        {stats.map(([label, value]) => (
          <div key={label} className="panel p-4">
            <p className="text-sm text-slate-500">{label}</p>
            <p className="mt-2 text-2xl font-bold text-slate-950">{value}</p>
          </div>
        ))}
      </div>
      <div className="grid gap-5 xl:grid-cols-3">
        <section className="panel p-5 xl:col-span-2">
          <h3 className="text-lg font-bold text-slate-950">按日执行成功率</h3>
          <Chart option={{
            tooltip: { trigger: 'axis' },
            grid: { left: 38, right: 18, top: 34, bottom: 34 },
            xAxis: { type: 'category', data: trend.map((item) => item.day) },
            yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
            series: [{ type: 'line', smooth: true, data: trend.map((item) => item.value), lineStyle: { color: '#10b981', width: 3 } }],
          }} />
        </section>
        <section className="panel p-5">
          <h3 className="text-lg font-bold text-slate-950">记忆使用情况</h3>
          <Chart option={{
            tooltip: { trigger: 'item' },
            series: [{ type: 'pie', radius: ['48%', '72%'], data: [
              { name: '命中 SQL Memory', value: runs.filter((run) => run.memory_hit).length },
              { name: '未命中 SQL Memory', value: runs.filter((run) => !run.memory_hit).length },
            ], color: ['#10b981', '#0891b2'] }],
          }} />
        </section>
      </div>
      <section className="panel overflow-hidden">
        <div className="border-b border-slate-200 p-5"><h3 className="text-lg font-bold text-slate-950">失败运行</h3></div>
        {failedRuns.length ? <DataTable data={failedRuns} columns={columns} /> : <p className="p-5 text-sm text-slate-500">当前加载的运行记录中没有失败项。</p>}
      </section>
    </div>
  );
}
