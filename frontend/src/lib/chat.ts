import { ApiError } from '../api/client';
import type { AnalysisResponse, ConversationMessage } from '../types/analysis';

export type ChatError = {
  message: string;
  status?: number;
  detail?: string;
};

export type ChatItem = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  sql?: string;
  rows?: AnalysisResponse['rows'];
  visualization?: AnalysisResponse['visualization'];
  metrics?: AnalysisResponse['metrics'];
  steps?: AnalysisResponse['steps'];
  error?: ChatError;
};

export type Session = {
  id: string;
  title: string;
  updatedAt: string;
  status: 'active' | 'waiting_for_clarification' | 'cancelled';
};

export function toChatError(error: unknown): ChatError {
  if (error instanceof ApiError) {
    if (error.status === 0) return { message: '暂时连不上本地分析服务，请确认后端服务已启动后再试。', status: error.status, detail: error.detail ?? error.message };
    if (error.status === 408) return { message: error.message || '服务响应超时，请重试或检查后端状态', status: error.status, detail: error.detail ?? error.message };
    if (error.status === 503) return { message: '模型未生成符合已确认业务口径的安全查询，系统未执行数据库。请稍后重试。', status: error.status, detail: error.detail ?? error.message };
    if (error.status >= 500) return { message: '分析服务暂时没有完成这次查询，请稍后重试。', status: error.status, detail: error.detail ?? error.message };
    return { message: error.message || '这次问题没有通过校验，请调整问题后再试。', status: error.status, detail: error.detail };
  }
  return { message: '分析过程被中断了，请稍后重试。' };
}

export function messageFromHistory(message: ConversationMessage): ChatItem {
  return {
    id: message.id,
    role: message.role,
    text: message.content,
    error: message.role === 'assistant' && message.response?.failure ? { message: message.content } : undefined,
  };
}

export function prependUnique(older: ChatItem[], current: ChatItem[]) {
  const ids = new Set(current.map((message) => message.id));
  return [...older.filter((message) => !ids.has(message.id)), ...current];
}
