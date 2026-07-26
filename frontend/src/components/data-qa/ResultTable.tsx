import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import { formatNumber } from '../../lib/format';
import type { AnalysisRow } from '../../types/analysis';

type ResultTableProps = {
  rows: AnalysisRow[];
};

export function ResultTable({ rows }: ResultTableProps) {
  const columns: ColumnDef<AnalysisRow>[] = Object.keys(rows[0] ?? {}).map((key) => ({
    accessorKey: key,
    header: key,
    cell: ({ getValue }) => {
      const value = getValue();
      return <span className="block font-mono">{typeof value === 'number' ? formatNumber(value) : String(value ?? '')}</span>;
    },
  }));
  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-stone-200 p-5">
        <h3 className="text-lg font-bold text-stone-900">查询结果明细</h3>
      </div>
      {rows.length ? <DataTable data={rows} columns={columns} /> : <p className="p-5 text-sm text-stone-500">暂无查询结果。</p>}
    </section>
  );
}
