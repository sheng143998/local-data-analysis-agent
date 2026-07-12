import { apiRequest } from './client';

export type UserMemory = {
  id: string;
  memory_key: string;
  category: string;
  value: Record<string, string>;
  status: 'active' | 'superseded' | 'revoked';
  version: number;
  created_at: string;
  updated_at: string;
};

export function listUserMemories() {
  return apiRequest<UserMemory[]>('/api/user-memories', { fallbackMessage: '读取长期偏好失败' });
}

export function deleteUserMemory(memoryKey: string) {
  return apiRequest<{ deleted: boolean }>(`/api/user-memories/${encodeURIComponent(memoryKey)}`, { method: 'DELETE', fallbackMessage: '删除长期偏好失败' });
}
