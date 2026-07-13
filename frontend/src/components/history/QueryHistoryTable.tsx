import { useEffect, useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import { listRuns } from '../../api/developerClient';
import type { QueryRunRecord } from '../../types/developer';

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value));
}

export function QueryHistoryTable() {
  const [runs, setRuns] = useState<QueryRunRecord[]>([]);
  const [selected, setSelected] = useState<QueryRunRecord | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    listRuns()
      .then((items) => {
        if (!active) return;
        setRuns(items);
        setSelected(items[0] ?? null);
      })
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : '读取运行记录失败'))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const filteredRuns = useMemo(
    () => runs.filter((run) => `${run.user_question} ${run.final_sql ?? ''}`.toLowerCase().includes(query.toLowerCase())),
    [query, runs],
  );
  const columns = useMemo<ColumnDef<QueryRunRecord>[]>(() => [
    { accessorKey: 'user_question', header: '提问内容' },
    { accessorKey: 'guard_status', header: '安全校验' },
    { accessorKey: 'execution_status', header: '执行状态' },
    { accessorKey: 'latency_ms', header: '耗时', cell: ({ getValue }) => `${getValue<number>()}ms` },
    { accessorKey: 'created_at', header: '创建时间', cell: ({ getValue }) => formatTime(getValue<string>()) },
    {
      id: 'action',
      header: '操作',
      cell: ({ row }) => <button type="button" className="font-semibold text-cyan-700" onClick={() => setSelected(row.original)}>查看</button>,
    },
  ], []);

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <section className="panel overflow-hidden">
        <div className="border-b border-slate-200 p-4">
          <input
            className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-cyan-600"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索问题或 SQL"
          />
        </div>
        {loading ? <p className="p-5 text-sm text-slate-500">正在读取真实运行记录...</p> : null}
        {error ? <p className="p-5 text-sm text-rose-700">{error}</p> : null}
        {!loading && !error && !filteredRuns.length ? <p className="p-5 text-sm text-slate-500">暂无可访问的运行记录。</p> : null}
        {!loading && !error && filteredRuns.length ? <DataTable data={filteredRuns} columns={columns} /> : null}
      </section>
      <aside className="panel p-5">
        <h3 className="text-lg font-bold text-slate-950">查询详情</h3>
        {!selected ? <p className="mt-3 text-sm text-slate-500">选择一条真实运行记录后查看详情。</p> : (
          <>
            <p className="mt-4 text-sm font-semibold text-slate-700">原始问题</p>
            <p className="mt-1 break-words text-sm text-slate-500">{selected.user_question}</p>
            <p className="mt-4 text-sm font-semibold text-slate-700">最终 SQL</p>
            <pre className="mt-2 max-h-52 overflow-auto rounded-md bg-slate-950 p-3 font-mono text-xs text-cyan-100">{selected.final_sql ?? '本次运行未生成可执行 SQL。'}</pre>
            <p className="mt-4 text-sm font-semibold text-slate-700">运行状态</p>
            <p className="mt-1 text-sm text-slate-500">Guard: {selected.guard_status}，执行: {selected.execution_status}，返回 {selected.row_count} 行</p>
            {selected.error_message ? <p className="mt-3 text-sm text-rose-700">{selected.error_message}</p> : null}
          </>
        )}
      </aside>
    </div>
  );
}
