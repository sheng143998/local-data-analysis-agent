import { Search } from 'lucide-react';
import { PageHeader } from '../components/common/PageHeader';
import { QueryHistoryTable } from '../components/history/QueryHistoryTable';

export function HistoryPage() {
  return (
    <>
      <PageHeader title="查询历史" description="查看每一次自然语言提问、最终 SQL、执行路径和结果摘要。" />
      <div className="mb-5 flex flex-wrap gap-3">
        <div className="flex min-w-72 flex-1 items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2">
          <Search className="h-4 w-4 text-slate-400" />
          <input className="w-full outline-none" placeholder="搜索问题或 SQL" />
        </div>
        {['执行成功', '执行失败', '今天', '本周', '本月'].map((filter) => (
          <button key={filter} className="secondary-btn">{filter}</button>
        ))}
      </div>
      <QueryHistoryTable />
    </>
  );
}
