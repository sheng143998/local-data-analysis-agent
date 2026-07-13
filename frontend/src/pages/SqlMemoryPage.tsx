import { PageHeader } from '../components/common/PageHeader';
import { SqlMemoryTable } from '../components/sql-memory/SqlMemoryTable';

export function SqlMemoryPage() {
  return (
    <>
      <PageHeader title="SQL 记忆" description="开发者与高级用户用于管理历史成功 SQL 模板、命中率和复用路径。" />
      <SqlMemoryTable />
    </>
  );
}
