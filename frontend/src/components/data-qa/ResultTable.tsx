import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import type { AnalysisRow } from '../../types/analysis';

type ResultTableProps = {
  rows: AnalysisRow[];
};

export function ResultTable({ rows }: ResultTableProps) {
  const columns: ColumnDef<AnalysisRow>[] = Object.keys(rows[0] ?? {}).map((key) => ({
    accessorKey: key,
    header: key,
    cell: ({ getValue }) => <span className="block font-mono">{String(getValue() ?? '')}</span>,
  }));
  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-slate-200 p-5">
        <h3 className="text-lg font-bold text-slate-950">查询结果明细</h3>
      </div>
      {rows.length ? <DataTable data={rows} columns={columns} /> : <p className="p-5 text-sm text-slate-500">暂无查询结果。</p>}
    </section>
  );
}
