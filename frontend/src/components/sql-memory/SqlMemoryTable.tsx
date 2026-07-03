import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import { finalSql, sqlMemoryRows } from '../../data/mock';

type MemoryRow = { question: string; intent: string; tables: string; success: string; fail: string; avg: string; last: string };
const data = sqlMemoryRows.map(([question, intent, tables, success, fail, avg, last]) => ({ question, intent, tables, success, fail, avg, last }));

const columns: ColumnDef<MemoryRow>[] = [
  { accessorKey: 'question', header: '典型问题' },
  { accessorKey: 'intent', header: '意图' },
  { accessorKey: 'tables', header: '使用数据表' },
  { accessorKey: 'success', header: '成功次数' },
  { accessorKey: 'fail', header: '失败次数' },
  { accessorKey: 'avg', header: '平均耗时' },
  { accessorKey: 'last', header: '最近使用时间' },
];

export function SqlMemoryTable() {
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
      <section className="panel overflow-hidden">
        <DataTable data={data} columns={columns} />
      </section>
      <aside className="panel p-5">
        <h3 className="text-lg font-bold text-slate-950">记忆详情</h3>
        <p className="mt-3 text-sm text-slate-500">问题模板：最近 {`{n}`} 天销售趋势</p>
        <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-950 p-3 font-mono text-xs text-cyan-100">{finalSql}</pre>
        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div className="sub-panel p-3"><p className="text-slate-500">参数 schema</p><b>n: number</b></div>
          <div className="sub-panel p-3"><p className="text-slate-500">向量相似度</p><b>0.93</b></div>
          <div className="sub-panel p-3"><p className="text-slate-500">历史运行</p><b>88 次</b></div>
          <div className="sub-panel p-3"><p className="text-slate-500">命中路径</p><b>fast_path</b></div>
        </div>
      </aside>
    </div>
  );
}
