'use client';

// Nhân sự — tách riêng khỏi Ứng viên (candidate_type=employee).
// Có cột Can Chi / cung hoàng đạo / năm sinh (chỉ hiện với hồ sơ đã opt-in EPA + có ngày sinh).

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useState } from 'react';

import { CandidateFormModal } from '@/components/features/candidate-form-modal';
import { DiscQuickAction } from '@/components/features/disc-quick-action';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api-client';
import type { Candidate } from '@/lib/types';

export default function EmployeesPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  const params = new URLSearchParams({
    page: String(page),
    per_page: '15',
    candidate_type: 'employee',
  });
  if (search) params.set('search', search);

  const { data, isLoading } = useQuery({
    queryKey: ['candidates', 'employees', page, search],
    queryFn: () => api.get<Candidate[]>(`/api/v1/candidates?${params}`),
  });
  const totalPages = data?.meta?.total_pages ?? 1;

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Nhân sự</h1>
          <p className="text-sm text-gray-500">{data?.meta?.total ?? 0} nhân sự</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>＋ Thêm nhân sự</Button>
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
              <th className="px-4 py-3">Mã NV</th>
              <th className="px-4 py-3">Bộ phận / Vị trí</th>
              <th className="px-4 py-3">Can Chi</th>
              <th className="px-4 py-3">Cung hoàng đạo</th>
              <th className="px-4 py-3">Năm sinh</th>
              <th className="px-4 py-3">DISC</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-gray-400">
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
                  <td className="px-4 py-3 text-gray-600">{c.employee_code ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {c.department ?? '—'}
                    {c.position ? ` · ${c.position}` : ''}
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {c.tuoi_am ?? '—'}
                    {c.menh ? <span className="text-xs text-gray-400"> · {c.menh}</span> : null}
                  </td>
                  <td className="px-4 py-3 text-gray-700">{c.cung_hoang_dao ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-600">{c.birth_year ?? '—'}</td>
                  <td className="px-4 py-3">
                    <DiscQuickAction candidate={c} />
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-gray-400">
                  Chưa có nhân sự nào
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-3">
          <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
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

      {showCreate && (
        <CandidateFormModal mode="create" defaultType="employee" onClose={() => setShowCreate(false)} />
      )}
    </div>
  );
}
