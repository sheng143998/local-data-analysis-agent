import type { AnalysisResponse, ConversationDetail, ConversationSummary } from '../types/analysis';
import { apiRequest } from './client';

export async function analyzeQuestion(question: string, conversationId?: string | null): Promise<AnalysisResponse> {
  return apiRequest<AnalysisResponse>('/api/analyze', {
    method: 'POST',
    body: { question, conversation_id: conversationId ?? null },
    fallbackMessage: '分析接口调用失败',
  });
}

export function listConversations() {
  return apiRequest<ConversationSummary[]>('/api/conversations', { fallbackMessage: '读取会话历史失败' });
}

export function getConversation(conversationId: string) {
  return apiRequest<ConversationDetail>(`/api/conversations/${conversationId}`, { fallbackMessage: '读取会话内容失败' });
}
