import { PageHeader } from '../components/common/PageHeader';
import { SettingsForm } from '../components/settings/SettingsForm';

export function SettingsPage() {
  return (
    <>
      <PageHeader title="系统设置" description="配置模型、数据库只读策略、安全白名单与 API Key。" />
      <SettingsForm />
    </>
  );
}
