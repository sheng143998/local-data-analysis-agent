import type { MetricDefinition, MetricPayload } from '../types/metric';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function listMetrics(): Promise<MetricDefinition[]> {
  const response = await fetch(`${API_BASE_URL}/api/metrics`);
  if (!response.ok) throw new Error('获取指标列表失败');
  return response.json();
}

export async function createMetric(payload: MetricPayload): Promise<MetricDefinition> {
  const response = await fetch(`${API_BASE_URL}/api/metrics`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('创建指标失败');
  return response.json();
}

export async function updateMetric(id: string, payload: Partial<MetricPayload>): Promise<MetricDefinition> {
  const response = await fetch(`${API_BASE_URL}/api/metrics/${id}`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('更新指标失败');
  return response.json();
}

export async function deleteMetric(id: string): Promise<{ deleted: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/metrics/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('删除指标失败');
  return response.json();
}
