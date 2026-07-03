import { PageHeader } from '../components/common/PageHeader';
import { ProfilePanel } from '../components/profile/ProfilePanel';

export function ProfilePage() {
  return (
    <>
      <PageHeader title="个人中心" description="查看账号资料、角色权限、常用数据表和查询使用情况。" />
      <ProfilePanel />
    </>
  );
}
