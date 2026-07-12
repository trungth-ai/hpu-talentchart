'use client';

// Trang Trắc nghiệm DISC — nơi tập trung gửi bài test DISC và theo dõi kết quả cho ứng viên/nhân sự.
// DISC vốn đã có sẵn nhưng bị "ẩn" trong trang chi tiết; trang này + mục menu giúp tìm & thao tác nhanh.

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useState } from 'react';

import { DiscQuickAction } from '@/components/features/disc-quick-action';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api-client';
import { STAGE_COLORS, STAGE_LABELS, TYPE_LABELS, type Candidate } from '@/lib/types';

export default function AssessmentsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  const params = new URLSearchParams({ page: String(page), per_page: '15' });
  if (search) params.set('search', search);

  const { data, isLoading } = useQuery({
    queryKey: ['candidates', 'assessments', page, search],
    queryFn: () => api.get<Candidate[]>(`/api/v1/candidates?${params}`),
  });

  const totalPages = data?.meta?.total_pages ?? 1;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">Trắc nghiệm DISC</h1>
        <p className="text-sm text-gray-500">
          Gửi bài test DISC và theo dõi kết quả tính cách của ứng viên &amp; nhân sự — thao tác ngay
          không cần mở từng hồ sơ.
        </p>
      </header>

      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          setSearch(searchInput);
          setPage(1);
        }}
      >
        <Input
          placeholder="Tìm theo tên hoặc email…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="w-64"
        />
        <Button type="submit" variant="secondary">
          Tìm
        </Button>
      </form>

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-100">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-100 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Họ tên</th>
              <th className="px-4 py-3">Loại</th>
              <th className="px-4 py-3">Trạng thái hồ sơ</th>
              <th className="px-4 py-3">DISC</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-gray-400">
                  Đang tải…
                </td>
              </tr>
            ) : data?.data?.length ? (
              data.data.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50/60">
                  <td className="px-4 py-3">
                    <Link
                      href={`/candidates/${c.id}`}
                      className="font-medium text-gray-900 hover:text-primary-700"
                    >
                      {c.full_name}
                    </Link>
                    <p className="text-xs text-gray-500">{c.email}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{TYPE_LABELS[c.candidate_type]}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STAGE_COLORS[c.pipeline_stage]}`}
                    >
                      {STAGE_LABELS[c.pipeline_stage]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <DiscQuickAction candidate={c} />
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-gray-400">
                  Không có hồ sơ nào
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Trước
          </Button>
          <span className="text-sm text-gray-500">
            Trang {page}/{totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Sau →
          </Button>
        </div>
      )}
    </div>
  );
}
