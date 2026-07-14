'use client';

// Portal tự phục vụ cho nhân sự/ứng viên: đăng nhập Google → tự làm bài DISC + xem kết quả.
// Token type=candidate (tách hoàn toàn token staff), lưu localStorage riêng. Chạy trên subdomain
// tổ chức ({slug}.hr.hpu.edu.vn) hoặc kèm "Mã tổ chức" trên tên miền phẳng.

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { GoogleLoginButton } from '@/components/features/google-login-button';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
const TOKEN_KEY = 'talentchart-candidate';

const DISC_NAMES: Record<string, string> = {
  D: 'Quyết đoán (D)',
  I: 'Ảnh hưởng (I)',
  S: 'Kiên định (S)',
  C: 'Chuẩn mực (C)',
};

interface MeProfile {
  full_name: string;
  email: string;
  pipeline_stage: string;
}
interface MyResult {
  disc_scores: Record<string, number>;
  disc_primary: string;
  disc_secondary: string;
  disc_profile: string;
}

export default function PortalPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [orgSlug, setOrgSlug] = useState('');
  const [me, setMe] = useState<MeProfile | null>(null);
  const [result, setResult] = useState<MyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(TOKEN_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setToken(parsed.token);
        setOrgSlug(parsed.orgSlug ?? '');
      }
    } catch {
      localStorage.removeItem(TOKEN_KEY);
    }
  }, []);

  const cFetch = async (path: string, tok: string, slug: string, opts: RequestInit = {}) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${tok}`,
      ...(opts.headers as Record<string, string>),
    };
    if (slug) headers['X-Org-Slug'] = slug;
    const res = await fetch(`${API_URL}${path}`, { ...opts, headers });
    const body = await res.json().catch(() => null);
    if (!res.ok || body?.status === 'error') {
      throw new Error(body?.message ?? 'Có lỗi xảy ra');
    }
    return body.data;
  };

  useEffect(() => {
    if (!token) return;
    cFetch('/api/v1/public/candidates/me', token, orgSlug)
      .then(setMe)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY); // token hỏng/hết hạn → đăng xuất
        setToken(null);
        setMe(null);
      });
    cFetch('/api/v1/public/candidates/me/result', token, orgSlug)
      .then(setResult)
      .catch(() => setResult(null)); // chưa có kết quả → bỏ qua
  }, [token, orgSlug]);

  const onLogin = (data: unknown) => {
    const d = data as { candidate_token: string };
    localStorage.setItem(TOKEN_KEY, JSON.stringify({ token: d.candidate_token, orgSlug }));
    setToken(d.candidate_token);
    setError(null);
  };

  const startTest = async () => {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      const data = await cFetch('/api/v1/public/candidates/me/test', token, orgSlug, {
        method: 'POST',
      });
      router.push(`/test/${data.token}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Không tạo được bài test');
    } finally {
      setBusy(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setMe(null);
    setResult(null);
  };

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <h1 className="mb-1 text-2xl font-bold text-primary-700">TalentChart · Cá nhân</h1>
      <p className="mb-6 text-sm text-gray-500">
        Tự đánh giá tính cách DISC và xem kết quả của bạn.
      </p>

      {error && <p className="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}

      {!token ? (
        <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100">
          <label className="mb-1 block text-sm text-gray-500">Mã tổ chức</label>
          <Input
            value={orgSlug}
            onChange={(e) => setOrgSlug(e.target.value)}
            placeholder="vd: hpu"
          />
          <p className="mt-1 text-xs text-gray-400">
            Bỏ trống nếu bạn truy cập qua tên miền riêng của tổ chức.
          </p>
          <GoogleLoginButton
            orgSlug={orgSlug}
            endpoint="/api/v1/public/auth/google"
            onSuccess={onLogin}
            onError={setError}
          />
        </div>
      ) : (
        <div className="space-y-5">
          <div className="flex items-center justify-between rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <div>
              <p className="font-semibold text-gray-900">{me?.full_name ?? '…'}</p>
              <p className="text-sm text-gray-500">{me?.email}</p>
            </div>
            <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-800">
              Đăng xuất
            </button>
          </div>

          <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <h2 className="mb-2 font-semibold text-gray-900">Bài test DISC</h2>
            <p className="mb-3 text-sm text-gray-600">
              Trắc nghiệm tính cách ~10 phút. Bạn có thể làm bất cứ lúc nào.
            </p>
            <Button onClick={startTest} disabled={busy}>
              {busy ? 'Đang chuẩn bị…' : result ? 'Làm lại bài test' : 'Bắt đầu làm bài test'}
            </Button>
          </div>

          {result && (
            <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
              <div className="mb-3 flex items-center gap-3">
                <h2 className="font-semibold text-gray-900">Kết quả của bạn</h2>
                <span className="rounded-full bg-primary-100 px-3 py-1 text-sm font-semibold text-primary-700">
                  {result.disc_profile}
                </span>
              </div>
              <div className="space-y-2">
                {(['D', 'I', 'S', 'C'] as const).map((d) => (
                  <div key={d} className="flex items-center gap-2">
                    <span className="w-32 text-xs text-gray-500">{DISC_NAMES[d]}</span>
                    <div className="h-2 flex-1 rounded-full bg-gray-100">
                      <div
                        className="h-2 rounded-full bg-primary-500"
                        style={{ width: `${result.disc_scores[d] ?? 0}%` }}
                      />
                    </div>
                    <span className="w-9 text-right text-xs text-gray-600">
                      {result.disc_scores[d] ?? 0}%
                    </span>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-gray-400">
                Kết quả EPA chỉ là tín hiệu tham khảo, không dùng làm yếu tố quyết định duy nhất.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
