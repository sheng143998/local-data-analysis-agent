import type { ColumnDef } from '@tanstack/react-table';
import { DataTable } from '../common/DataTable';
import { salesTrend } from '../../data/mock';

type ResultRow = (typeof salesTrend)[number];

const columns: ColumnDef<ResultRow>[] = [
  { accessorKey: 'date', header: '日期' },
  { accessorKey: 'amount', header: '日销售额', cell: ({ getValue }) => <span className="block text-right font-mono">¥{Number(getValue()).toLocaleString()}</span> },
  { accessorKey: 'orders', header: '订单数', cell: ({ getValue }) => <span className="block text-right font-mono">{Number(getValue()).toLocaleString()}</span> },
  { accessorKey: 'avg', header: '平均客单价', cell: ({ getValue }) => <span className="block text-right font-mono">¥{Number(getValue()).toLocaleString()}</span> },
  { accessorKey: 'refundRate', header: '退款率', cell: ({ getValue }) => <span className="block text-right font-mono">{String(getValue())}</span> },
];

export function ResultTable() {
  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-slate-200 p-5">
        <h3 className="text-lg font-bold text-slate-950">查询结果明细</h3>
      </div>
      <DataTable data={salesTrend.slice(-12)} columns={columns} />
    </section>
  );
}
