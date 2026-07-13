import { PageHeader } from '../components/common/PageHeader';
import { QueryHistoryTable } from '../components/history/QueryHistoryTable';

export function HistoryPage() {
  return (
    <>
      <PageHeader title="查询历史" description="查看每一次自然语言提问、最终 SQL、执行路径和结果摘要。" />
      <QueryHistoryTable />
    </>
  );
}
