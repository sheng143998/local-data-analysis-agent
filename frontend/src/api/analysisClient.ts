import type { AnalysisResponse, ConversationDetail, ConversationListPage } from '../types/analysis';
import { apiRequest } from './client';

export async function analyzeQuestion(question: string, conversationId?: string | null): Promise<AnalysisResponse> {
  return apiRequest<AnalysisResponse>('/api/analyze', {
    method: 'POST',
    body: { question, conversation_id: conversationId ?? null },
    fallbackMessage: '分析接口调用失败',
  });
}

export function listConversations(cursor?: string | null) {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : '';
  return apiRequest<ConversationListPage>(`/api/conversations${query}`, { fallbackMessage: '读取会话历史失败' });
}

export function getConversation(conversationId: string, before?: string | null) {
  const query = before ? `?before=${encodeURIComponent(before)}` : '';
  return apiRequest<ConversationDetail>(`/api/conversations/${conversationId}${query}`, { fallbackMessage: '读取会话内容失败' });
}

export function claimDevelopmentConversations() {
  return apiRequest<{ claimed: number }>('/api/conversations/claim-development', {
    method: 'POST',
    fallbackMessage: '迁移本机历史失败',
  });
}
