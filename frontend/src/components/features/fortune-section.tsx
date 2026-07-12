'use client';

// Vận trình ngày/tháng (2.1/2.2) — Can Chi tính offline + Claude diễn giải,
// kèm nút "Cào lichngaytot" (chỉ gọi khi người dùng bấm).

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { api, ApiError } from '@/lib/api-client';
import type { FortuneResult, LichngaytotResult } from '@/lib/types';

// Ngày hôm nay theo giờ máy (người dùng ở VN → trùng ngày VN), định dạng YYYY-MM-DD
function todayLocal(): string {
  return new Date().toLocaleDateString('en-CA');
}

// Dịch chuỗi ngày YYYY-MM-DD đi `days` ngày
function shiftDate(iso: string, days: number): string {
  const d = new Date(iso + 'T00:00:00');
  d.setDate(d.getDate() + days);
  return d.toLocaleDateString('en-CA');
}

// Hiển thị DD/MM/YYYY (quy ước hiển thị ngày của dự án)
function formatViewDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
}

export function FortuneSection({ candidateId }: { candidateId: string }) {
  const { data: res, isLoading, isError } = useQuery({
    queryKey: ['candidate', candidateId, 'fortune'],
    queryFn: () => api.get<FortuneResult>(`/api/v1/epa/candidates/${candidateId}/fortune`),
    retry: false,
  });
  const f = res?.data;

  const [lnt, setLnt] = useState<LichngaytotResult | null>(null);
  const [lntErr, setLntErr] = useState<string | null>(null);
  const [lntLoading, setLntLoading] = useState(false);
  const todayStr = todayLocal();
  const [viewDate, setViewDate] = useState<string>(todayStr);

  if (isError) return null; // ứng viên chưa đủ điều kiện (consent + ngày sinh) → ẩn
  if (!f || isLoading)
    return (
      <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
        <h2 className="mb-2 font-semibold text-gray-900">Vận trình</h2>
        <p className="text-sm text-gray-400">Đang tải vận trình (có thể mất vài giây khi gọi AI)…</p>
      </section>
    );

  const fetchLichngaytot = async () => {
    setLntLoading(true);
    setLntErr(null);
    try {
      const r = await api.get<LichngaytotResult>(
        `/api/v1/epa/candidates/${candidateId}/lichngaytot?date=${viewDate}`
      );
      setLnt(r.data);
    } catch (e) {
      setLntErr(e instanceof ApiError ? e.message : 'Không lấy được dữ liệu, thử lại sau');
    } finally {
      setLntLoading(false);
    }
  };

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

      <div className="mt-4 border-t border-gray-100 pt-3">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-gray-600">Tử vi ngày:</span>
          <Button variant="secondary" size="sm" onClick={() => setViewDate((d) => shiftDate(d, -1))}>
            ‹ Hôm trước
          </Button>
          <input
            type="date"
            value={viewDate}
            max={todayStr}
            onChange={(e) => e.target.value && setViewDate(e.target.value)}
            className="h-9 rounded-lg border border-gray-300 px-2 text-sm"
          />
          <Button
            variant="secondary"
            size="sm"
            disabled={viewDate >= todayStr}
            onClick={() => setViewDate((d) => shiftDate(d, 1))}
          >
            Hôm sau ›
          </Button>
          <Button size="sm" disabled={lntLoading} onClick={fetchLichngaytot}>
            {lntLoading ? 'Đang tải…' : '🔮 Xem tử vi ngày này'}
          </Button>
        </div>
        <p className="text-[11px] text-gray-400">
          Dữ liệu được cào tự động hằng ngày và lưu lại — có thể xem các ngày trước.
        </p>
        {lntErr && <p className="mt-2 text-sm text-amber-700">{lntErr}</p>}
        {lnt && (
          <div className="mt-3 space-y-3">
            <p className="text-xs text-gray-500">Tử vi ngày {formatViewDate(lnt.date)}</p>
            {(
              [
                ['Ngày tốt/xấu · sao · giờ hoàng đạo', lnt.day],
                ['Tử vi theo tuổi', lnt.zodiac_day],
                ['Tử vi theo cung', lnt.horoscope_day],
              ] as const
            ).map(([label, blk]) =>
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
