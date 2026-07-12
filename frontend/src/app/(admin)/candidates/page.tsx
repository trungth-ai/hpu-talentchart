'use client';

// Danh sách ứng viên & nhân sự (Sprint 7) — search, filter stage/type, pagination
// + Thêm nhân sự (mở modal CRUD)

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { CandidateFormModal } from '@/components/features/candidate-form-modal';
import { DiscQuickAction } from '@/components/features/disc-quick-action';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api } from '@/lib/api-client';
import {
  PIPELINE_STAGES,
  STAGE_COLORS,
  STAGE_LABELS,
  TYPE_LABELS,
  type Candidate,
} from '@/lib/types';
import { formatDate } from '@/lib/utils';

function CandidatesContent() {
  const searchParams = useSearchParams();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [stage, setStage] = useState(searchParams.get('stage') ?? '');
  const [type, setType] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  const params = new URLSearchParams({ page: String(page), per_page: '15' });
  if (search) params.set('search', search);
  if (stage) params.set('pipeline_stage', stage);
  if (type) params.set('candidate_type', type);

  const { data, isLoading } = useQuery({
    queryKey: ['candidates', 'list', page, search, stage, type],
    queryFn: () => api.get<Candidate[]>(`/api/v1/candidates?${params}`),
  });

  const totalPages = data?.meta?.total_pages ?? 1;

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ứng viên & Nhân sự</h1>
          <p className="text-sm text-gray-500">{data?.meta?.total ?? 0} hồ sơ</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>＋ Thêm nhân sự</Button>
      </header>

      {/* Bộ lọc */}
      <div className="flex flex-wrap items-center gap-3">
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
        <select
          value={stage}
          onChange={(e) => {
            setStage(e.target.value);
            setPage(1);
          }}
          className="h-10 rounded-lg border border-gray-300 bg-white px-3 text-sm"
        >
          <option value="">Mọi trạng thái</option>
          {PIPELINE_STAGES.map((s) => (
            <option key={s} value={s}>
              {STAGE_LABELS[s]}
            </option>
          ))}
        </select>
        <select
          value={type}
          onChange={(e) => {
            setType(e.target.value);
            setPage(1);
          }}
          className="h-10 rounded-lg border border-gray-300 bg-white px-3 text-sm"
        >
          <option value="">Mọi loại</option>
          {Object.entries(TYPE_LABELS).map(([k, v]) => (
            <option key={k} value={k}>
              {v}
            </option>
          ))}
        </select>
      </div>

      {/* Bảng */}
      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-100">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-100 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Họ tên</th>
              <th className="px-4 py-3">Loại</th>
              <th className="px-4 py-3">Bộ phận / Vị trí</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3">DISC</th>
              <th className="px-4 py-3">Ngày tạo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
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
                  <td className="px-4 py-3 text-gray-600">
                    {TYPE_LABELS[c.candidate_type]}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {c.department ?? '—'}
                    {c.position ? ` · ${c.position}` : ''}
                  </td>
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
                  <td className="px-4 py-3 text-gray-500">{formatDate(c.created_at)}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
                  Không có hồ sơ nào khớp bộ lọc
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Phân trang */}
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

      {showCreate && <CandidateFormModal mode="create" onClose={() => setShowCreate(false)} />}
    </div>
  );
}

export default function CandidatesPage() {
  return (
    <Suspense fallback={<div className="py-10 text-center text-gray-400">Đang tải…</div>}>
      <CandidatesContent />
    </Suspense>
  );
}
