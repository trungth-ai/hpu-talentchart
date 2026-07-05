'use client';

// Tin tuyển dụng (Sprint 7) — danh sách + tạo + đăng/gỡ khỏi Career Page

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api, ApiError } from '@/lib/api-client';
import type { JobPost } from '@/lib/types';
import { formatDate, formatVND } from '@/lib/utils';

interface FormState {
  title: string;
  location: string;
  salary_min: string;
  salary_max: string;
  description: string;
}

const EMPTY_FORM: FormState = {
  title: '',
  location: '',
  salary_min: '',
  salary_max: '',
  description: '',
};

export default function JobPostsPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['job-posts', 'list'],
    queryFn: () => api.get<JobPost[]>('/api/v1/job-posts?per_page=50'),
  });

  const create = useMutation({
    mutationFn: () =>
      api.post<JobPost>('/api/v1/job-posts', {
        title: form.title,
        location: form.location || null,
        salary_min: form.salary_min ? parseInt(form.salary_min, 10) : null,
        salary_max: form.salary_max ? parseInt(form.salary_max, 10) : null,
        description: form.description || null,
      }),
    onSuccess: () => {
      setShowForm(false);
      setForm(EMPTY_FORM);
      setFormError(null);
      queryClient.invalidateQueries({ queryKey: ['job-posts'] });
    },
    onError: (e) => setFormError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  const togglePublish = useMutation({
    mutationFn: ({ id, publish }: { id: string; publish: boolean }) =>
      api.post(`/api/v1/job-posts/${id}/${publish ? 'publish' : 'unpublish'}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['job-posts'] }),
  });

  return (
    <div className="space-y-5">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tin tuyển dụng</h1>
          <p className="text-sm text-gray-500">
            {data?.meta?.total ?? 0} tin · tin đã đăng hiển thị trên Career Page công khai
          </p>
        </div>
        <Button onClick={() => setShowForm((v) => !v)}>
          {showForm ? 'Đóng form' : '+ Tạo tin'}
        </Button>
      </header>

      {showForm && (
        <form
          className="grid gap-4 rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate();
          }}
        >
          <div className="sm:col-span-2">
            <Label htmlFor="j-title">Tiêu đề *</Label>
            <Input
              id="j-title"
              required
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Giảng viên Công nghệ thông tin"
            />
          </div>
          <div>
            <Label htmlFor="j-location">Địa điểm</Label>
            <Input
              id="j-location"
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              placeholder="Hải Phòng"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="j-salmin">Lương từ (VNĐ)</Label>
              <Input
                id="j-salmin"
                type="number"
                min={0}
                step={500000}
                value={form.salary_min}
                onChange={(e) => setForm({ ...form, salary_min: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="j-salmax">Lương đến (VNĐ)</Label>
              <Input
                id="j-salmax"
                type="number"
                min={0}
                step={500000}
                value={form.salary_max}
                onChange={(e) => setForm({ ...form, salary_max: e.target.value })}
              />
            </div>
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="j-desc">Mô tả công việc</Label>
            <textarea
              id="j-desc"
              rows={4}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
              placeholder="Mô tả trách nhiệm, yêu cầu…"
            />
          </div>
          {formError && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">
              {formError}
            </p>
          )}
          <div>
            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? 'Đang tạo…' : 'Tạo tin (dạng nháp)'}
            </Button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-100">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-100 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Tin tuyển dụng</th>
              <th className="px-4 py-3">Mức lương</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3">Ngày đăng</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-gray-400">
                  Đang tải…
                </td>
              </tr>
            ) : data?.data?.length ? (
              data.data.map((j) => (
                <tr key={j.id} className="hover:bg-gray-50/60">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{j.title}</p>
                    <p className="text-xs text-gray-500">
                      /{j.slug}
                      {j.location ? ` · ${j.location}` : ''}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {j.salary_min == null && j.salary_max == null
                      ? 'Thỏa thuận'
                      : `${formatVND(j.salary_min)} – ${formatVND(j.salary_max)}`}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        j.is_published
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {j.is_published ? 'Đang đăng' : 'Nháp'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(j.published_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="sm"
                      variant={j.is_published ? 'secondary' : 'primary'}
                      disabled={togglePublish.isPending}
                      onClick={() =>
                        togglePublish.mutate({ id: j.id, publish: !j.is_published })
                      }
                    >
                      {j.is_published ? 'Gỡ tin' : 'Đăng tin'}
                    </Button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-gray-400">
                  Chưa có tin tuyển dụng nào
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
