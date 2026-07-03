import { PageHeader } from '../components/common/PageHeader';
import { EvaluationDashboard } from '../components/evaluation/EvaluationDashboard';

export function EvaluationPage() {
  return (
    <>
      <PageHeader title="评估报告" description="跟踪 SQL 生成、查询执行、记忆复用和失败案例修复情况。" />
      <EvaluationDashboard />
    </>
  );
}
