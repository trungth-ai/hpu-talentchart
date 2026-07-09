'use client';

// Modal "Xem thêm" — hiển thị TOÀN DIỆN nội dung tử vi (con giáp + cung hoàng đạo)
// lấy từ bảng astrology_reference (nạp nguyên văn từ tài liệu nguồn).

import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { api } from '@/lib/api-client';
import type { AstrologyRef } from '@/lib/types';

interface Props {
  diaChi?: string; // địa chi (Tý, Sửu, ...) — có thì hiện tab con giáp
  animalLabel?: string; // "Tuổi Lợn"
  horoscopeCode: string; // ARIES, ...
  horoscopeName: string; // Bạch Dương, ...
  onClose: () => void;
}

function tabCls(active: boolean): string {
  return `-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
    active
      ? 'border-primary-600 text-primary-700'
      : 'border-transparent text-gray-500 hover:text-gray-700'
  }`;
}

export function AstrologyDetailModal({
  diaChi,
  animalLabel,
  horoscopeCode,
  horoscopeName,
  onClose,
}: Props) {
  const [tab, setTab] = useState<'zodiac' | 'horoscope'>(diaChi ? 'zodiac' : 'horoscope');

  const zodiac = useQuery({
    queryKey: ['astro', 'zodiac', diaChi],
    queryFn: () =>
      api.get<AstrologyRef>(`/api/v1/epa/reference/zodiac/${encodeURIComponent(diaChi!)}`),
    enabled: Boolean(diaChi) && tab === 'zodiac',
    retry: false,
  });
  const horoscope = useQuery({
    queryKey: ['astro', 'horoscope', horoscopeCode],
    queryFn: () => api.get<AstrologyRef>(`/api/v1/epa/reference/horoscope/${horoscopeCode}`),
    enabled: tab === 'horoscope',
    retry: false,
  });

  const notLoaded = (
    <p className="py-6 text-center text-sm text-gray-400">
      Chưa nạp dữ liệu chi tiết. Chạy <code>scripts/seed_astrology.py</code> trên máy chủ.
    </p>
  );
  const loading = <p className="py-6 text-center text-sm text-gray-400">Đang tải…</p>;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 py-8"
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-gray-100 p-4">
          <h2 className="text-lg font-bold text-gray-900">Xem toàn diện — Tử vi</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Đóng"
          >
            ✕
          </button>
        </div>

        <div className="flex gap-2 border-b border-gray-100 px-4">
          {diaChi && (
            <button type="button" onClick={() => setTab('zodiac')} className={tabCls(tab === 'zodiac')}>
              {animalLabel ?? 'Con giáp'}
            </button>
          )}
          <button
            type="button"
            onClick={() => setTab('horoscope')}
            className={tabCls(tab === 'horoscope')}
          >
            Cung {horoscopeName}
          </button>
        </div>

        <div className="overflow-y-auto p-5">
          {tab === 'zodiac' &&
            (zodiac.data?.data ? (
              <article className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
                {zodiac.data.data.content.full}
              </article>
            ) : zodiac.isError ? (
              notLoaded
            ) : (
              loading
            ))}

          {tab === 'horoscope' &&
            (horoscope.data?.data ? (
              <div className="space-y-5">
                {horoscope.data.data.content.book1 && (
                  <section>
                    <h3 className="mb-1 text-sm font-semibold text-primary-700">
                      Theo sách “12 Chòm Sao Và Đời Người”
                    </h3>
                    <article className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
                      {horoscope.data.data.content.book1}
                    </article>
                  </section>
                )}
                {horoscope.data.data.content.tuvitay && (
                  <section>
                    <h3 className="mb-1 text-sm font-semibold text-primary-700">
                      Theo sách “Tử Vi Tây”
                    </h3>
                    <article className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
                      {horoscope.data.data.content.tuvitay}
                    </article>
                  </section>
                )}
              </div>
            ) : horoscope.isError ? (
              notLoaded
            ) : (
              loading
            ))}
        </div>

        <div className="border-t border-gray-100 p-3 text-right">
          <Button variant="secondary" onClick={onClose}>
            Đóng
          </Button>
        </div>
      </div>
    </div>
  );
}
