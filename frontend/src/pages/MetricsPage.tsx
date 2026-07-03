import { PageHeader } from '../components/common/PageHeader';
import { MetricDefinitionCards } from '../components/metrics/MetricDefinitionCards';

export function MetricsPage() {
  return (
    <>
      <PageHeader
        title="指标口径"
        description="维护团队统一的业务指标。新增、编辑或停用指标后，数据问答会按这里的口径理解问题。"
      />
      <MetricDefinitionCards />
    </>
  );
}
