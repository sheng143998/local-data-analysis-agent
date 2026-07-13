import type { AnalysisResponse, ConversationDetail, ConversationListPage } from '../types/analysis';
import { ApiError, apiRequest, getApiBaseUrl, getCookie } from './client';

type StreamHandlers = {
  onStage: (stage: { name: string; status: string }) => void;
  onResult: (result: AnalysisResponse) => void;
};

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

export async function streamAnalyzeQuestion(
  question: string,
  conversationId: string | null,
  handlers: StreamHandlers,
  signal: AbortSignal,
) {
  const headers: HeadersInit = { 'content-type': 'application/json' };
  const csrfToken = getCookie('local_data_agent_csrf');
  if (csrfToken) headers['X-CSRF-Token'] = csrfToken;

  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/api/analyze/stream`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify({ question, conversation_id: conversationId }),
      signal,
    });
  } catch (error) {
    if (signal.aborted) throw error;
    throw new ApiError('分析流连接失败，请确认本地服务已启动', 0);
  }

  if (!response.ok) throw new ApiError('分析流服务暂时不可用，请稍后重试', response.status);
  if (!response.body) throw new ApiError('分析流响应不可读取', 0);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let receivedDone = false;
  while (!receivedDone) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replaceAll('\r\n', '\n');
    const events = buffer.split('\n\n');
    buffer = events.pop() ?? '';
    for (const block of events) {
      const parsed = parseSseEvent(block);
      if (!parsed) continue;
      if (parsed.event === 'stage') handlers.onStage(parsed.data as { name: string; status: string });
      if (parsed.event === 'result') handlers.onResult(parsed.data as AnalysisResponse);
      if (parsed.event === 'error') {
        const data = parsed.data as { status?: number; detail?: string };
        throw new ApiError(data.detail || '分析流服务暂时不可用，请稍后重试', data.status ?? 500);
      }
      if (parsed.event === 'done') receivedDone = true;
    }
    if (done && !receivedDone) throw new ApiError('分析流意外中断，请稍后重试', 0);
  }
}

function parseSseEvent(block: string): { event: string; data: unknown } | null {
  const fields = block.split('\n');
  const event = fields.find((line) => line.startsWith('event:'))?.slice(6).trim();
  const data = fields.find((line) => line.startsWith('data:'))?.slice(5).trim();
  if (!event || !data) return null;
  try {
    return { event, data: JSON.parse(data) };
  } catch {
    throw new ApiError('分析流响应格式无效', 0);
  }
}
