type ApiRequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  fallbackMessage: string;
};

type FastApiErrorBody = {
  detail?: unknown;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

function buildUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

export function getCookie(name: string): string | undefined {
  const prefix = `${encodeURIComponent(name)}=`;
  const item = document.cookie.split('; ').find((value) => value.startsWith(prefix));
  return item ? decodeURIComponent(item.slice(prefix.length)) : undefined;
}

async function readJsonSafely(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;

  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

function summarizeValidationDetail(detail: unknown): string | undefined {
  if (!Array.isArray(detail)) return undefined;

  const firstMessage = detail
    .map((item) => {
      if (item && typeof item === 'object' && 'msg' in item) {
        const message = (item as { msg?: unknown }).msg;
        return typeof message === 'string' ? message : undefined;
      }
      return undefined;
    })
    .find(Boolean);

  return firstMessage ? `请求参数不完整或格式不正确：${firstMessage}` : '请求参数不完整或格式不正确';
}

function getSafeErrorMessage(status: number, fallbackMessage: string, errorBody: unknown) {
  const body = errorBody as FastApiErrorBody | undefined;
  const detail = body?.detail;

  if (typeof detail === 'string' && status < 500) {
    return { message: detail, detail };
  }

  const validationMessage = summarizeValidationDetail(detail);
  if (validationMessage && status === 422) {
    return { message: validationMessage, detail: validationMessage };
  }

  if (status === 401) {
    return { message: '登录状态已失效，请重新登录', detail: undefined };
  }

  if (status === 403) {
    return { message: '当前账号没有权限执行此操作', detail: undefined };
  }

  if (status === 404) {
    return { message: '请求的资源不存在或已被删除', detail: undefined };
  }

  if (status >= 500) {
    return { message: `${fallbackMessage}，服务暂时不可用，请稍后重试`, detail: undefined };
  }

  return { message: fallbackMessage, detail: undefined };
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions): Promise<T> {
  const headers: HeadersInit = {};
  const init: RequestInit = {
    method: options.method ?? 'GET',
    headers,
    credentials: 'include',
  };

  if (init.method !== 'GET') {
    const csrfToken = getCookie('local_data_agent_csrf');
    if (csrfToken) headers['X-CSRF-Token'] = csrfToken;
  }

  if (options.body !== undefined) {
    headers['content-type'] = 'application/json';
    init.body = JSON.stringify(options.body);
  }

  try {
    const response = await fetch(buildUrl(path), init);
    const payload = await readJsonSafely(response);

    if (!response.ok) {
      const error = getSafeErrorMessage(response.status, options.fallbackMessage, payload);
      throw new ApiError(error.message, response.status, error.detail);
    }

    return payload as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    throw new ApiError(`${options.fallbackMessage}，请确认本地服务已启动`, 0);
  }
}
