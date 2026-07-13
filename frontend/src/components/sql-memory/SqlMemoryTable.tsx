import { useEffect, useMemo, useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import { listSqlMemories } from '../../api/developerClient';
import type { SqlMemoryRecord } from '../../types/developer';

function formatTime(value: string | null) {
  return value ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '-';
}

export function SqlMemoryTable() {
  const [memories, setMemories] = useState<SqlMemoryRecord[]>([]);
  const [selected, setSelected] = useState<SqlMemoryRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    listSqlMemories()
      .then((items) => {
        if (!active) return;
        setMemories(items);
        setSelected(items[0] ?? null);
      })
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : '读取 SQL 记忆失败'))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  const columns = useMemo<ColumnDef<SqlMemoryRecord>[]>(() => [
    { accessorKey: 'canonical_question', header: '典型问题' },
    { accessorKey: 'intent', header: '意图' },
    { accessorKey: 'tables', header: '使用数据表', cell: ({ getValue }) => getValue<string[]>().join(', ') || '-' },
    { accessorKey: 'trust_status', header: '可信状态' },
    { accessorKey: 'success_count', header: '成功次数' },
    { accessorKey: 'failure_count', header: '失败次数' },
    { accessorKey: 'avg_latency_ms', header: '平均耗时', cell: ({ getValue }) => `${getValue<number>()}ms` },
    { accessorKey: 'last_used_at', header: '最近使用', cell: ({ getValue }) => formatTime(getValue<string | null>()) },
    { id: 'action', header: '操作', cell: ({ row }) => <button type="button" className="font-semibold text-cyan-700" onClick={() => setSelected(row.original)}>查看</button> },
  ], []);

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
      <section className="panel overflow-hidden">
        {loading ? <p className="p-5 text-sm text-slate-500">正在读取真实 SQL 记忆...</p> : null}
        {error ? <p className="p-5 text-sm text-rose-700">{error}</p> : null}
        {!loading && !error && !memories.length ? <p className="p-5 text-sm text-slate-500">暂无可访问的 SQL 记忆。</p> : null}
        {!loading && !error && memories.length ? <DataTable data={memories} columns={columns} /> : null}
      </section>
      <aside className="panel p-5">
        <h3 className="text-lg font-bold text-slate-950">记忆详情</h3>
        {!selected ? <p className="mt-3 text-sm text-slate-500">选择一条真实 SQL Memory 后查看详情。</p> : (
          <>
            <p className="mt-3 text-sm text-slate-500">问题模板：{selected.question_pattern || selected.canonical_question}</p>
            <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-950 p-3 font-mono text-xs text-cyan-100">{selected.final_sql}</pre>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div className="sub-panel p-3"><p className="text-slate-500">可信状态</p><b>{selected.trust_status}</b></div>
              <div className="sub-panel p-3"><p className="text-slate-500">返回列</p><b>{selected.last_result_columns.length}</b></div>
              <div className="sub-panel p-3"><p className="text-slate-500">历史运行</p><b>{selected.success_count + selected.failure_count} 次</b></div>
              <div className="sub-panel p-3"><p className="text-slate-500">平均耗时</p><b>{selected.avg_latency_ms}ms</b></div>
            </div>
          </>
        )}
      </aside>
    </div>
  );
}
