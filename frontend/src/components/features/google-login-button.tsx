'use client';

// Nút đăng nhập Google (ADR-004) — dùng Google Identity Services (GIS)
// Chỉ hiển thị khi có NEXT_PUBLIC_GOOGLE_CLIENT_ID. GIS trả id_token → gửi backend.

import { useEffect, useRef, useState } from 'react';

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? '';
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8003';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: object) => void;
          renderButton: (el: HTMLElement, options: object) => void;
        };
      };
    };
  }
}

interface Props {
  // Slug tổ chức (dev/domain chính); production subdomain tự resolve
  orgSlug: string;
  // Đích API: staff = /auth/google, ứng viên = /public/auth/google
  endpoint?: string;
  onSuccess: (data: unknown) => void;
  onError: (message: string) => void;
}

export function GoogleLoginButton({
  orgSlug,
  endpoint = '/api/v1/auth/google',
  onSuccess,
  onError,
}: Props) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const [scriptReady, setScriptReady] = useState(false);
  // orgSlug thay đổi theo form — dùng ref để callback GIS luôn đọc giá trị mới nhất
  const orgSlugRef = useRef(orgSlug);
  orgSlugRef.current = orgSlug;

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    if (window.google?.accounts) {
      setScriptReady(true);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.onload = () => setScriptReady(true);
    document.head.appendChild(script);
  }, []);

  useEffect(() => {
    if (!scriptReady || !buttonRef.current || !window.google) return;

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: async (response: { credential: string }) => {
        try {
          const headers: Record<string, string> = { 'Content-Type': 'application/json' };
          if (orgSlugRef.current) headers['X-Org-Slug'] = orgSlugRef.current;
          const res = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ id_token: response.credential }),
          });
          const body = await res.json();
          if (!res.ok || body.status === 'error') {
            onError(body.message ?? 'Đăng nhập Google thất bại');
            return;
          }
          onSuccess(body.data);
        } catch {
          onError('Không kết nối được máy chủ, vui lòng thử lại');
        }
      },
    });
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: 'outline',
      size: 'large',
      width: 336,
      text: 'signin_with',
      locale: 'vi',
    });
  }, [scriptReady, endpoint, onSuccess, onError]);

  // Chưa cấu hình Google OAuth → không hiển thị gì
  if (!GOOGLE_CLIENT_ID) return null;

  return (
    <div>
      <div className="my-4 flex items-center gap-3 text-xs text-gray-400">
        <div className="h-px flex-1 bg-gray-200" />
        hoặc
        <div className="h-px flex-1 bg-gray-200" />
      </div>
      <div ref={buttonRef} className="flex justify-center" />
      <p className="mt-2 text-center text-xs text-gray-400">
        Dành cho tài khoản Google của tổ chức (VD: @hpu.edu.vn)
      </p>
    </div>
  );
}
