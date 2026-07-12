import { useEffect, useState } from 'react';
import { Trash2 } from 'lucide-react';
import { useAuth } from '../../auth/AuthProvider';
import { deleteUserMemory, listUserMemories, type UserMemory } from '../../api/userMemoryClient';

export function ProfilePanel() {
  const { user, logout } = useAuth();
  const [memories, setMemories] = useState<UserMemory[]>([]);
  const [error, setError] = useState('');
  useEffect(() => { listUserMemories().then(setMemories).catch((caught) => setError(caught instanceof Error ? caught.message : '读取长期偏好失败')); }, []);
  const remove = async (memoryKey: string) => {
    try { await deleteUserMemory(memoryKey); setMemories((current) => current.filter((memory) => memory.memory_key !== memoryKey)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : '删除长期偏好失败'); }
  };
  return <div className="grid gap-5 xl:grid-cols-[340px_1fr]">
    <section className="panel p-6"><div className="grid h-20 w-20 place-items-center rounded-md bg-slate-950 text-2xl font-bold text-cyan-200">{user?.display_name.slice(0, 1).toUpperCase()}</div><h3 className="mt-5 text-xl font-bold text-slate-950">{user?.display_name}</h3><p className="text-sm text-slate-500">{user?.email}</p><div className="mt-5 text-sm"><p><span className="text-slate-500">角色：</span>{user?.role === 'admin' ? '管理员' : '分析师'}</p></div><button onClick={() => void logout()} className="primary-btn mt-6 bg-rose-600 hover:bg-rose-500">退出登录</button></section>
    <section className="panel p-6"><div className="flex items-center justify-between"><h3 className="text-lg font-bold text-slate-950">长期偏好</h3><span className="text-xs text-slate-500">只保存明确要求记住的偏好</span></div>{error && <p className="mt-4 text-sm text-rose-600">{error}</p>}<div className="mt-5 divide-y divide-slate-100">{memories.length === 0 ? <p className="py-4 text-sm text-slate-500">暂无长期偏好。</p> : memories.map((memory) => <div key={memory.id} className="flex items-center justify-between gap-4 py-4"><div><p className="font-medium text-slate-900">{memory.value.label ?? memory.memory_key}</p><p className="mt-1 text-xs text-slate-500">版本 {memory.version}，更新于 {new Date(memory.updated_at).toLocaleString()}</p></div><button onClick={() => void remove(memory.memory_key)} title="删除偏好" className="icon-btn text-rose-600 hover:bg-rose-50"><Trash2 className="h-4 w-4" /></button></div>)}</div></section>
  </div>;
}
