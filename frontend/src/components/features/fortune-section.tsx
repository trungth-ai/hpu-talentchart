'use client';

// Vận trình: (1) AI diễn giải ngày/tháng (Can Chi offline + Claude); (2) tử vi cào lichngaytot
// theo KỲ (Ngày/Tuần/Tháng/Năm) — ĐỌC TỪ DB (cào tự động định kỳ; kỳ hiện tại thiếu thì cào bù).

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { api } from '@/lib/api-client';
import type { FortuneResult, LichngaytotResult } from '@/lib/types';

type Period = 'day' | 'week' | 'month' | 'year';
const PERIOD_TABS: { value: Period; label: string }[] = [
  { value: 'day', label: 'Ngày' },
  { value: 'week', label: 'Tuần' },
  { value: 'month', label: 'Tháng' },
  { value: 'year', label: 'Năm' },
];

function todayLocal(): string {
  return new Date().toLocaleDateString('en-CA');
}

// Dịch chuỗi ngày YYYY-MM-DD đi 1 kỳ (theo period) — để xem kỳ trước/sau
function shiftPeriod(iso: string, period: Period, dir: number): string {
  const d = new Date(iso + 'T00:00:00');
  if (period === 'day') d.setDate(d.getDate() + dir);
  else if (period === 'week') d.setDate(d.getDate() + 7 * dir);
  else if (period === 'month') d.setMonth(d.getMonth() + dir);
  else d.setFullYear(d.getFullYear() + dir);
  return d.toLocaleDateString('en-CA');
}

export function FortuneSection({ candidateId }: { candidateId: string }) {
  const { data: res, isLoading, isError } = useQuery({
    queryKey: ['candidate', candidateId, 'fortune'],
    queryFn: () => api.get<FortuneResult>(`/api/v1/epa/candidates/${candidateId}/fortune`),
    retry: false,
  });
  const f = res?.data;

  const todayStr = todayLocal();
  const [period, setPeriod] = useState<Period>('day');
  const [viewDate, setViewDate] = useState<string>(todayStr);
  const [started, setStarted] = useState(false);

  const {
    data: lntRes,
    isFetching: lntLoading,
    error: lntError,
  } = useQuery({
    queryKey: ['candidate', candidateId, 'lichngaytot', period, viewDate],
    queryFn: () =>
      api.get<LichngaytotResult>(
        `/api/v1/epa/candidates/${candidateId}/lichngaytot?period=${period}&date=${viewDate}`
      ),
    enabled: started,
    retry: false,
  });
  const lnt = lntRes?.data;

  if (isError) return null; // ứng viên chưa đủ điều kiện (consent + ngày sinh) → ẩn
  if (!f || isLoading)
    return (
      <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
        <h2 className="mb-2 font-semibold text-gray-900">Vận trình</h2>
        <p className="text-sm text-gray-400">
          Đang tải vận trình (có thể mất vài giây khi gọi AI)…
        </p>
      </section>
    );

  const blocks: [string, LichngaytotResult['zodiac']][] = !lnt
    ? []
    : period === 'day'
      ? [
          ['Ngày tốt/xấu · sao · giờ hoàng đạo', lnt.day ?? null],
          ['Tử vi theo tuổi', lnt.zodiac],
          ['Tử vi theo cung', lnt.horoscope],
        ]
      : [
          ['Tử vi theo tuổi', lnt.zodiac],
          ['Tử vi theo cung', lnt.horoscope],
        ];

  const periodLabel = PERIOD_TABS.find((t) => t.value === period)?.label;

  return (
    <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold text-gray-900">Vận trình</h2>
        {!f.ai_generated && (
          <span className="text-xs text-amber-600">
            Chưa cấu hình ANTHROPIC_API_KEY — đang hiển thị dữ kiện gốc
          </span>
        )}
      </div>

      {/* AI diễn giải ngày + tháng (Can Chi tính offline) */}
      <div className="space-y-4 text-sm">
        <div>
          <h3 className="mb-1 text-xs font-semibold uppercase text-primary-600">
            Hôm nay · {f.day.canchi.solar_date} · ngày {f.day.canchi.day_canchi}, năm{' '}
            {f.day.canchi.year_canchi}
          </h3>
          <p className="leading-relaxed text-gray-700">{f.day.narrative}</p>
        </div>
        <div>
          <h3 className="mb-1 text-xs font-semibold uppercase text-primary-600">
            Tháng {f.month.month}/{f.month.year}
          </h3>
          <p className="leading-relaxed text-gray-700">{f.month.narrative}</p>
          {f.month.book_guidance && (
            <details className="mt-1 text-xs text-gray-500">
              <summary className="cursor-pointer hover:text-gray-700">
                Chỉ nam theo sách (tháng {f.month.month})
              </summary>
              <p className="mt-1 whitespace-pre-wrap leading-relaxed">{f.month.book_guidance}</p>
            </details>
          )}
        </div>
      </div>

      {/* Tử vi lichngaytot theo kỳ — đọc từ DB (cào tự động định kỳ) */}
      <div className="mt-4 border-t border-gray-100 pt-3">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-gray-600">Tử vi theo kỳ:</span>
          <div className="flex overflow-hidden rounded-lg border border-gray-200">
            {PERIOD_TABS.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => {
                  setPeriod(t.value);
                  setViewDate(todayStr);
                  setStarted(true);
                }}
                className={`px-3 py-1.5 text-sm transition-colors ${
                  period === t.value && started
                    ? 'bg-primary-600 text-white'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {started && (
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setViewDate((d) => shiftPeriod(d, period, -1))}
            >
              ‹ Kỳ trước
            </Button>
            <span className="text-xs text-gray-500">
              {lnt ? `${periodLabel}: ${lnt.period_key}` : '…'}
            </span>
            <Button
              variant="secondary"
              size="sm"
              disabled={viewDate >= todayStr}
              onClick={() => setViewDate((d) => shiftPeriod(d, period, 1))}
            >
              Kỳ sau ›
            </Button>
          </div>
        )}

        {!started ? (
          <p className="text-xs text-gray-500">
            Chọn một kỳ ở trên để xem tử vi (đọc từ dữ liệu đã cào tự động).
          </p>
        ) : lntLoading ? (
          <p className="mt-2 text-sm text-gray-400">Đang tải…</p>
        ) : lntError ? (
          <p className="mt-2 text-sm text-amber-700">
            Chưa có dữ liệu tử vi cho kỳ này (dữ liệu được cào tự động định kỳ).
          </p>
        ) : (
          <div className="mt-2 space-y-3">
            {blocks.map(([label, blk]) =>
              blk ? (
                <div key={label}>
                  <p className="text-xs font-semibold text-primary-700">{label}</p>
                  {blk.url && (
                    <a
                      href={blk.url}
                      target="_blank"
                      rel="noreferrer"
                      className="break-all text-[11px] text-primary-500 hover:underline"
                    >
                      {blk.url}
                    </a>
                  )}
                  <p className="mt-1 max-h-52 overflow-y-auto whitespace-pre-wrap rounded-lg bg-gray-50 p-3 text-xs text-gray-600">
                    {blk.excerpt}
                  </p>
                </div>
              ) : null
            )}
          </div>
        )}
      </div>

      <p className="mt-3 text-xs text-gray-400">{f.disclaimer}</p>
    </section>
  );
}
