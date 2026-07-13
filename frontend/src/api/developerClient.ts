import { apiRequest } from './client';
import type { QueryRunRecord, SqlMemoryRecord } from '../types/developer';

/** 管理员观测接口只返回已脱敏的运行和记忆元数据。 */
export function listRuns(limit = 50) {
  return apiRequest<QueryRunRecord[]>(`/api/runs?limit=${limit}`, {
    fallbackMessage: '读取运行记录失败',
  });
}

/** SQL Memory 仅面向管理员，普通用户不应看到伪造的模板数据。 */
export function listSqlMemories(limit = 50) {
  return apiRequest<SqlMemoryRecord[]>(`/api/memories?limit=${limit}`, {
    fallbackMessage: '读取 SQL 记忆失败',
  });
}
