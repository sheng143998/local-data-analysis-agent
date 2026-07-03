import type { MetricDefinition, MetricPayload } from '../types/metric';
import { apiRequest } from './client';

export async function listMetrics(): Promise<MetricDefinition[]> {
  return apiRequest<MetricDefinition[]>('/api/metrics', {
    fallbackMessage: '获取指标列表失败',
  });
}

export async function createMetric(payload: MetricPayload): Promise<MetricDefinition> {
  return apiRequest<MetricDefinition>('/api/metrics', {
    method: 'POST',
    body: payload,
    fallbackMessage: '创建指标失败',
  });
}

export async function updateMetric(id: string, payload: Partial<MetricPayload>): Promise<MetricDefinition> {
  return apiRequest<MetricDefinition>(`/api/metrics/${id}`, {
    method: 'PUT',
    body: payload,
    fallbackMessage: '更新指标失败',
  });
}

export async function deleteMetric(id: string): Promise<{ deleted: boolean }> {
  return apiRequest<{ deleted: boolean }>(`/api/metrics/${id}`, {
    method: 'DELETE',
    fallbackMessage: '删除指标失败',
  });
}
