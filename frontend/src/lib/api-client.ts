// API client — gắn JWT vào header, tự refresh token khi 401 (Sprint 1)
// Mọi response theo envelope {status, data, message[, meta]} (api-conventions.md)

import { useAuthStore } from '@/stores/auth';

// Mặc định same-origin ('') — /api/* được next.config rewrites chuyển tiếp vào backend.
// Chỉ set NEXT_PUBLIC_API_URL khi API nằm ở origin khác (hiếm).
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

export interface ApiEnvelope<T> {
  status: 'success' | 'error';
  data: T;
  message: string;
  meta?: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  };
  code?: string;
  errors?: { field: string; message: string }[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public httpStatus: number,
    public errors: { field: string; message: string }[] = []
  ) {
    super(message);
  }
}

// Refresh đồng thời chỉ chạy 1 lần (tránh race khi nhiều request cùng 401)
let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  const { refreshToken, setTokens, logout } = useAuthStore.getState();
  if (!refreshToken) return false;

  refreshPromise ??= (async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) {
        logout();
        return false;
      }
      const body = (await res.json()) as ApiEnvelope<{
        access_token: string;
        refresh_token: string;
      }>;
      setTokens(body.data.access_token, body.data.refresh_token);
      return true;
    } catch {
      logout();
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  retried = false
): Promise<ApiEnvelope<T>> {
  const { accessToken } = useAuthStore.getState();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  // Access token hết hạn → thử refresh 1 lần rồi gọi lại
  if (response.status === 401 && !retried && useAuthStore.getState().refreshToken) {
    const refreshed = await tryRefreshToken();
    if (refreshed) return apiFetch<T>(path, options, true);
  }

  const body = (await response.json().catch(() => null)) as ApiEnvelope<T> | null;

  if (!response.ok || body?.status === 'error') {
    throw new ApiError(
      body?.message ?? 'Lỗi kết nối máy chủ, vui lòng thử lại',
      body?.code ?? 'NETWORK_ERROR',
      response.status,
      body?.errors ?? []
    );
  }

  return body as ApiEnvelope<T>;
}

// Helpers tiện dụng
export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, data?: unknown) =>
    apiFetch<T>(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined }),
  put: <T>(path: string, data: unknown) =>
    apiFetch<T>(path, { method: 'PUT', body: JSON.stringify(data) }),
  patch: <T>(path: string, data: unknown) =>
    apiFetch<T>(path, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(path: string) => apiFetch<T>(path, { method: 'DELETE' }),
};
