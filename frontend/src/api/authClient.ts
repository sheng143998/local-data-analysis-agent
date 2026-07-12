import { apiRequest } from './client';
import type { AuthResponse } from '../types/auth';

export function login(payload: { email: string; password: string }) {
  return apiRequest<AuthResponse>('/api/auth/login', { method: 'POST', body: payload, fallbackMessage: '登录失败' });
}

export function register(payload: { email: string; display_name: string; password: string }) {
  return apiRequest<AuthResponse>('/api/auth/register', { method: 'POST', body: payload, fallbackMessage: '注册失败' });
}

export function getCurrentUser() {
  return apiRequest<AuthResponse>('/api/auth/me', { fallbackMessage: '读取登录状态失败' });
}

export function logout() {
  return apiRequest<void>('/api/auth/logout', { method: 'POST', fallbackMessage: '退出登录失败' });
}
