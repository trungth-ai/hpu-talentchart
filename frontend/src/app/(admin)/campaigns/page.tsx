'use client';

// Đợt tuyển dụng (Sprint 7) — danh sách + tạo/sửa inline form

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api, ApiError } from '@/lib/api-client';
import type { Campaign } from '@/lib/types';
import { formatDate, formatVND } from '@/lib/utils';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Nháp',
  open: 'Đang mở',
  closed: 'Đã đóng',
};
const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-700',
  open: 'bg-green-100 text-green-700',
  closed: 'bg-red-100 text-red-700',
};

interface FormState {
  name: string;
  position: string;
  department: string;
  target_headcount: number;
  salary_min: string;
  salary_max: string;
  end_date: string;
}

const EMPTY_FORM: FormState = {
  name: '',
  position: '',
  department: '',
  target_headcount: 1,
  salary_min: '',
  salary_max: '',
  end_date: '',
};

export default function CampaignsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['campaigns', 'list'],
    queryFn: () => api.get<Campaign[]>('/api/v1/campaigns?per_page=50'),
  });

  const create = useMutation({
    mutationFn: () =>
      api.post<Campaign>('/api/v1/campaigns', {
        name: form.name,
        position: form.position,
        department: form.department || null,
        target_headcount: form.target_headcount,
        // Lương Integer VNĐ — parse từ input text
        salary_min: form.salary_min ? parseInt(form.salary_min, 10) : null,
        salary_max: form.salary_max ? parseInt(form.salary_max, 10) : null,
        end_date: form.end_date || null,
      }),
    onSuccess: () => {
      setShowForm(false);
      setForm(EMPTY_FORM);
      setFormError(null);
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
    onError: (e) => setFormError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.put<Campaign>(`/api/v1/campaigns/${id}`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['campaigns'] }),
  });

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Đợt tuyển dụng</h1>
          <p className="text-sm text-gray-500">{data?.meta?.total ?? 0} đợt tuyển</p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Đóng form' : '+ Tạo đợt tuyển'}
        </Button>
      </header>

      {showForm && (
        <form
          className="grid gap-4 rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100 sm:grid-cols-2 lg:grid-cols-3"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <div>
            <Label htmlFor="c-name">Tên đợt tuyển *</Label>
            <Input
              id="c-name"
              required
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Tuyển giảng viên CNTT 2026"
            />
          </div>
          <div>
            <Label htmlFor="c-position">Vị trí *</Label>
            <Input
              id="c-position"
              required
              value={form.position}
              onChange={(e) => setForm({ ...form, position: e.target.value })}
              placeholder="Giảng viên"
            />
          </div>
          <div>
            <Label htmlFor="c-dept">Bộ phận</Label>
            <Input
              id="c-dept"
              value={form.department}
              onChange={(e) => setForm({ ...form, department: e.target.value })}
              placeholder="Khoa CNTT"
            />
          </div>
          <div>
            <Label htmlFor="c-headcount">Chỉ tiêu</Label>
            <Input
              id="c-headcount"
              type="number"
              min={1}
              value={form.target_headcount}
              onChange={(e) =>
                setForm({ ...form, target_headcount: parseInt(e.target.value || '1', 10) })
              }
            />
          </div>
          <div>
            <Label htmlFor="c-salmin">Lương từ (VNĐ)</Label>
            <Input
              id="c-salmin"
              type="number"
              min={0}
              step={500000}
              value={form.salary_min}
              onChange={(e) => setForm({ ...form, salary_min: e.target.value })}
              placeholder="15000000"
            />
          </div>
          <div>
            <Label htmlFor="c-salmax">Lương đến (VNĐ)</Label>
            <Input
              id="c-salmax"
              type="number"
              min={0}
              step={500000}
              value={form.salary_max}
              onChange={(e) => setForm({ ...form, salary_max: e.target.value })}
              placeholder="25000000"
            />
          </div>
          <div>
            <Label htmlFor="c-end">Hạn kết thúc</Label>
            <Input
              id="c-end"
              type="date"
              value={form.end_date}
              onChange={(e) => setForm({ ...form, end_date: e.target.value })}
            />
          </div>
          {formError && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2 lg:col-span-3">
              {formError}
            </p>
          )}
          <div className="flex items-end">
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? 'Đang tạo…' : 'Tạo đợt tuyển'}
            </Button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-100">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-100 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Đợt tuyển</th>
              <th className="px-4 py-3">Chỉ tiêu</th>
              <th className="px-4 py-3">Mức lương</th>
              <th className="px-4 py-3">Hạn</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3"></th>
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
                    <p className="font-medium text-gray-900">{c.name}</p>
                    <p className="text-xs text-gray-500">
                      {c.position}
                      {c.department ? ` · ${c.department}` : ''}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{c.target_headcount}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {c.salary_min == null && c.salary_max == null
                      ? 'Thỏa thuận'
                      : `${formatVND(c.salary_min)} – ${formatVND(c.salary_max)}`}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(c.end_date)}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[c.status] ?? 'bg-gray-100 text-gray-600'}`}
                    >
                      {STATUS_LABELS[c.status] ?? c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {c.status === 'draft' && (
                      <Button
                        size="sm"
                        onClick={() => updateStatus.mutate({ id: c.id, status: 'open' })}
                      >
                        Mở đợt tuyển
                      </Button>
                    )}
                    {c.status === 'open' && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => updateStatus.mutate({ id: c.id, status: 'closed' })}
                      >
                        Đóng
                      </Button>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
                  Chưa có đợt tuyển nào — bấm “Tạo đợt tuyển” để bắt đầu
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
