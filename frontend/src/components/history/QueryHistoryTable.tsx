import { useState } from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import { finalSql, historyRows } from '../../data/mock';

type HistoryRow = {
  question: string;
  path: string;
  tables: string;
  time: string;
  status: string;
  createdAt: string;
};

const data: HistoryRow[] = historyRows.map(([question, path, tables, time, status, createdAt]) => ({
  question, path, tables, time, status, createdAt,
}));

const columns: ColumnDef<HistoryRow>[] = [
  { accessorKey: 'question', header: '提问内容' },
  { accessorKey: 'path', header: '执行路径' },
  { accessorKey: 'tables', header: '使用数据表' },
  { accessorKey: 'time', header: '查询耗时' },
  { accessorKey: 'status', header: '执行状态', cell: ({ getValue }) => <span className={String(getValue()).includes('成功') ? 'text-emerald-600' : 'text-rose-600'}>{String(getValue())}</span> },
  { accessorKey: 'createdAt', header: '创建时间' },
  { id: 'action', header: '操作', cell: () => <button className="font-semibold text-cyan-700">查看</button> },
];

export function QueryHistoryTable() {
  const [open, setOpen] = useState(false);
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_360px]">
      <button className="panel overflow-hidden text-left" onClick={() => setOpen(true)}>
        <DataTable data={data} columns={columns} />
      </button>
      <aside className={`panel p-5 transition ${open ? 'translate-x-0 opacity-100' : 'translate-x-2 opacity-90'}`}>
        <h3 className="text-lg font-bold text-slate-950">查询详情</h3>
        <p className="mt-4 text-sm font-semibold text-slate-700">原始问题</p>
        <p className="mt-1 text-sm text-slate-500">最近 30 天销售额按天变化如何？</p>
        <p className="mt-4 text-sm font-semibold text-slate-700">最终 SQL</p>
        <pre className="mt-2 max-h-52 overflow-auto rounded-md bg-slate-950 p-3 font-mono text-xs text-cyan-100">{finalSql}</pre>
        <p className="mt-4 text-sm font-semibold text-slate-700">数据来源</p>
        <p className="mt-1 text-sm text-slate-500">orders、payments、refunds</p>
        <p className="mt-4 text-sm font-semibold text-slate-700">查询结果摘要</p>
        <p className="mt-1 text-sm text-slate-500">销售额环比提升 12.4%，支付成功率稳定。</p>
        <button className="primary-btn mt-5 w-full">重新运行</button>
      </aside>
    </div>
  );
}
