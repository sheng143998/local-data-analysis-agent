import type { AnalysisResponse } from '../types/analysis';
import { apiRequest } from './client';

export async function analyzeQuestion(question: string): Promise<AnalysisResponse> {
  return apiRequest<AnalysisResponse>('/api/analyze', {
    method: 'POST',
    body: { question },
    fallbackMessage: '分析接口调用失败',
  });
}
