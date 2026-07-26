import { Sparkles, Table2 } from 'lucide-react';
import { ErrorBoundary } from '../common/ErrorBoundary';
import { AnswerPanel } from '../data-qa/AnswerPanel';
import { ResultChart } from '../data-qa/ResultChart';
import { AnalysisDetails } from './AnalysisDetails';
import { formatCurrency, formatNumber } from '../../lib/format';
import type { ChatError, ChatItem } from '../../lib/chat';
import type { AnalysisRow, AnalysisValue } from '../../types/analysis';

const columnLabels: Record<string, string> = {
  order_date: '日期',
  month: '月份',
  daily_sales: '销售额',
  sales_amount: '销售额',
  order_count: '订单数',
  avg_order_value: '平均客单价',
  refund_rate: '退款率',
  success_rate: '成功率',
  failure_rate: '失败率',
  gross_margin: '毛利率',
  repeat_rate: '复购率',
  category_label: '品类',
  product_label: '商品',
  city_label: '城市',
  payment_method_label: '支付方式',
  segment_label: '分组',
};

function getResultColumns(rows: AnalysisRow[]) {
  const seen = new Set<string>();
  rows.forEach((row) => Object.keys(row).forEach((key) => seen.add(key)));
  return Array.from(seen).slice(0, 6);
}

function formatColumnLabel(column: string) {
  return columnLabels[column] ?? column.replaceAll('_', ' ');
}

function isNumericLike(value: AnalysisValue) {
  return typeof value === 'number';
}

function formatCellValue(column: string, value: AnalysisValue) {
  if (value === null || value === undefined || value === '') return '--';
  if (typeof value === 'boolean') return value ? '是' : '否';
  if (typeof value !== 'number') {
    const text = String(value);
    if ((column.includes('date') || column.includes('month')) && /^\d{4}-\d{2}-\d{2}T/.test(text)) {
      return column.includes('month') ? text.slice(0, 7) : text.slice(0, 10);
    }
    return text;
  }
  if (column.includes('rate') || column.includes('margin')) return `${value.toFixed(2)}%`;
  if (column.includes('sales') || column.includes('amount') || column.includes('value')) return formatCurrency(value);
  return formatNumber(value);
}

function ResultTable({ rows }: { rows: AnalysisRow[] }) {
  const columns = getResultColumns(rows);
  if (!columns.length) return null;
  return (
    <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-soft">
      <div className="flex items-center gap-2 border-b border-stone-100 px-4 py-3 text-sm font-semibold text-stone-800">
        <Table2 className="h-4 w-4 text-accent" /> 查询结果
      </div>
      <div className="max-h-80 overflow-auto">
        <table className="w-full min-w-[620px] text-sm">
          <thead className="bg-stone-50 text-left text-xs text-stone-500">
            <tr>
              {columns.map((column) => <th key={column} className="px-4 py-3 font-medium">{formatColumnLabel(column)}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr key={`${index}-${String(row[columns[0]] ?? '')}`} className="border-t border-stone-100 transition hover:bg-stone-50">
                {columns.map((column) => (
                  <td key={column} className={['px-4 py-3 text-stone-700', isNumericLike(row[column]) ? 'nums text-right' : ''].join(' ')}>
                    {formatCellValue(column, row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ErrorCard({ error }: { error: ChatError }) {
  return (
    <div className="rounded-2xl border border-warning/40 bg-warning-soft p-4">
      <p className="text-sm font-semibold text-stone-800">本次分析未完成</p>
      <p className="mt-1 text-sm leading-6 text-stone-600">{error.message}</p>
      {error.status ? <p className="mt-2 text-xs text-stone-400">参考编号：{error.status}</p> : null}
    </div>
  );
}

type MessageBubbleProps = {
  message: ChatItem;
};

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <div className="ml-auto max-w-3xl rounded-[18px] rounded-br-md bg-accent-100 px-4 py-3 text-sm leading-6 text-stone-900">
        {message.text}
      </div>
    );
  }

  const hasAnalysis = Boolean(message.sql || message.rows?.length || message.metrics?.length);

  return (
    <div className="mx-auto flex max-w-5xl gap-3">
      <div className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-accent text-white">
        <Sparkles className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1 space-y-4">
        {message.error ? (
          <ErrorCard error={message.error} />
        ) : hasAnalysis ? (
          <AnswerPanel summary={message.text} metrics={message.metrics ?? []} />
        ) : (
          <div className="text-sm leading-7 text-stone-700">{message.text}</div>
        )}
        {hasAnalysis ? (
          <ErrorBoundary title="分析结果渲染出错">
            <div className="space-y-4">
              {message.rows?.length && message.visualization ? <ResultChart rows={message.rows} visualization={message.visualization} /> : null}
              {message.rows?.length ? <ResultTable rows={message.rows.slice(0, 30)} /> : null}
              <AnalysisDetails sql={message.sql} steps={message.steps} />
            </div>
          </ErrorBoundary>
        ) : null}
      </div>
    </div>
  );
}
