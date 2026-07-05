'use client';

// Dashboard (Sprint 7) — pipeline stats + đợt tuyển đang mở + ứng viên mới nhất

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';

import { api } from '@/lib/api-client';
import {
  STAGE_COLORS,
  STAGE_LABELS,
  TYPE_LABELS,
  type Campaign,
  type Candidate,
} from '@/lib/types';
import { formatDate } from '@/lib/utils';

export default function DashboardPage() {
  const { data: stats } = useQuery({
    queryKey: ['candidates', 'stats'],
    queryFn: () => api.get<Record<string, number>>('/api/v1/candidates/stats'),
  });

  const { data: openCampaigns } = useQuery({
    queryKey: ['campaigns', 'open'],
    queryFn: () => api.get<Campaign[]>('/api/v1/campaigns?status=open&per_page=5'),
  });

  const { data: recentCandidates } = useQuery({
    queryKey: ['candidates', 'recent'],
    queryFn: () => api.get<Candidate[]>('/api/v1/candidates?per_page=6'),
  });

  // EPA hôm nay — chỉ hiện khi tenant bật Eastern Layer (lỗi 422 → ẩn)
  const { data: epaToday } = useQuery({
    queryKey: ['epa', 'today'],
    queryFn: () => api.get<{ lunar_date: string; year_canchi: string; day_canchi: string }>(
      '/api/v1/epa/today'
    ),
    retry: false,
  });

  const total = Object.values(stats?.data ?? {}).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-8">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tổng quan</h1>
          <p className="text-sm text-gray-500">
            {total} hồ sơ đang hoạt động trong hệ thống
          </p>
        </div>
        {epaToday?.data && (
          <div className="rounded-xl bg-white px-4 py-2 text-right text-sm shadow-sm ring-1 ring-gray-100">
            <p className="text-gray-500">
              Âm lịch {epaToday.data.lunar_date} · Năm {epaToday.data.year_canchi}
            </p>
            <p className="font-medium text-primary-700">
              Ngày {epaToday.data.day_canchi}
            </p>
          </div>
        )}
      </header>

      {/* Pipeline */}
      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
          Pipeline tuyển dụng
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
          {Object.entries(STAGE_LABELS).map(([stage, label]) => (
            <Link
              key={stage}
              href={`/candidates?stage=${stage}`}
              className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-gray-100 transition-shadow hover:shadow"
            >
              <p className="text-xs text-gray-500">{label}</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">
                {stats?.data?.[stage] ?? 0}
              </p>
            </Link>
          ))}
        </div>
      </section>

      <div className="grid gap-6 lg:grid--cols-2 lg:grid-cols-2">
        {/* Đợt tuyển đang mở */}
        <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Đợt tuyển đang mở</h2>
            <Link href="/campaigns" className="text-sm text-primary-600 hover:underline">
              Xem tất cả →
            </Link>
          </div>
          {openCampaigns?.data?.length ? (
            <ul className="divide-y divide-gray-50">
              {openCampaigns.data.map((c) => (
                <li key={c.id} className="flex items-center justify-between py-2.5">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{c.name}</p>
                    <p className="text-xs text-gray-500">
                      {c.position} · chỉ tiêu {c.target_headcount}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    đến {formatDate(c.end_date)}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-gray-400">
              Chưa có đợt tuyển nào đang mở
            </p>
          )}
        </section>

        {/* Hồ sơ mới nhất */}
        <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">Hồ sơ mới nhất</h2>
            <Link href="/candidates" className="text-sm text-primary-600 hover:underline">
              Xem tất cả →
            </Link>
          </div>
          {recentCandidates?.data?.length ? (
            <ul className="divide-y divide-gray-50">
              {recentCandidates.data.map((c) => (
                <li key={c.id} className="flex items-center justify-between py-2.5">
                  <Link href={`/candidates/${c.id}`} className="min-w-0">
                    <p className="truncate text-sm font-medium text-gray-900 hover:text-primary-700">
                      {c.full_name}
                    </p>
                    <p className="truncate text-xs text-gray-500">
                      {TYPE_LABELS[c.candidate_type]} · {c.position ?? c.department ?? '—'}
                    </p>
                  </Link>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${STAGE_COLORS[c.pipeline_stage]}`}
                  >
                    {STAGE_LABELS[c.pipeline_stage]}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-6 text-center text-sm text-gray-400">Chưa có hồ sơ nào</p>
          )}
        </section>
      </div>
    </div>
  );
}
