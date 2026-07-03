import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import { sourceRows } from '../../data/mock';

type SourceRow = { name: string; desc: string; rows: string; updatedAt: string; vectorized: string };
const data: SourceRow[] = sourceRows.map(([name, desc, rows, updatedAt, vectorized]) => ({ name, desc, rows, updatedAt, vectorized }));

const columns: ColumnDef<SourceRow>[] = [
  { accessorKey: 'name', header: '数据表' },
  { accessorKey: 'desc', header: '中文说明' },
  { accessorKey: 'rows', header: '行数', cell: ({ getValue }) => <span className="block text-right font-mono">{String(getValue())}</span> },
  { accessorKey: 'updatedAt', header: '最近更新时间' },
  { accessorKey: 'vectorized', header: '是否已向量化' },
  { id: 'action', header: '操作', cell: () => <button className="font-semibold text-cyan-700">查看字段</button> },
];

export function DataSourceTable() {
  return (
    <section className="panel overflow-hidden">
      <DataTable data={data} columns={columns} />
    </section>
  );
}
