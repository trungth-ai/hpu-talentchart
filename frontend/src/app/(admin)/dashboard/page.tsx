'use client';

// Dashboard tối giản (Sprint 1) — xác nhận đăng nhập + thống kê pipeline
// Dashboard đầy đủ sẽ làm ở Sprint 7

import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { Button } from '@/components/ui/button';
import { api } from '@/lib/api-client';
import { useAuthStore, type AuthUser } from '@/stores/auth';

const STAGE_LABELS: Record<string, string> = {
  NEW: 'Mới',
  SCREENING: 'Sàng lọc',
  TEST_SENT: 'Đã gửi bài test',
  TEST_DONE: 'Hoàn thành test',
  INTERVIEW: 'Phỏng vấn',
  DECISION: 'Chờ quyết định',
  HIRED: 'Đã tuyển',
  REJECTED: 'Từ chối',
};

export default function DashboardPage() {
  const router = useRouter();
  const { accessToken, user, logout } = useAuthStore();

  useEffect(() => {
    if (!accessToken) router.replace('/login');
  }, [accessToken, router]);

  const { data: me } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => api.get<AuthUser>('/api/v1/auth/me'),
    enabled: Boolean(accessToken),
  });

  const { data: stats } = useQuery({
    queryKey: ['candidates', 'stats'],
    queryFn: () => api.get<Record<string, number>>('/api/v1/candidates/stats'),
    enabled: Boolean(accessToken),
  });

  const displayUser = me?.data ?? user;
  if (!accessToken) return null;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-primary-700">TalentChart</h1>
          <p className="text-sm text-gray-500">
            Xin chào, <span className="font-medium">{displayUser?.full_name}</span>
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => {
            logout();
            router.replace('/login');
          }}
        >
          Đăng xuất
        </Button>
      </header>

      <section>
        <h2 className="mb-4 text-lg font-semibold">Pipeline ứng viên</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Object.entries(STAGE_LABELS).map(([stage, label]) => (
            <div
              key={stage}
              className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-100"
            >
              <p className="text-sm text-gray-500">{label}</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                {stats?.data?.[stage] ?? 0}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
