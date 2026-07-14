'use client';

// Cơ cấu tổ chức — cây phòng ban + trưởng đơn vị. Chỉ owner/admin (backend chốt require_admin).

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { AdminTabs } from '@/components/features/admin-tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api, ApiError } from '@/lib/api-client';
import type { Department, OrgUser } from '@/lib/types';
import { useAuthStore } from '@/stores/auth';

// Xếp danh sách phẳng thành thứ tự cây (cha trước con) + độ sâu để thụt lề
function orderTree(deps: Department[]): { dep: Department; depth: number }[] {
  const byParent = new Map<string | null, Department[]>();
  for (const d of deps) {
    const k = d.parent_id;
    if (!byParent.has(k)) byParent.set(k, []);
    byParent.get(k)!.push(d);
  }
  const out: { dep: Department; depth: number }[] = [];
  const walk = (parent: string | null, depth: number) => {
    for (const d of byParent.get(parent) ?? []) {
      out.push({ dep: d, depth });
      walk(d.id, depth + 1);
    }
  };
  walk(null, 0);
  return out;
}

const EMPTY = { name: '', parent_id: '', manager_user_id: '' };

export default function DepartmentsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const isAdmin = ['owner', 'admin'].includes(user?.org_role ?? '');
  const [form, setForm] = useState(EMPTY);
  const [editId, setEditId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: depsRes } = useQuery({
    queryKey: ['departments'],
    queryFn: () => api.get<Department[]>('/api/v1/departments'),
    enabled: isAdmin,
  });
  const { data: usersRes } = useQuery({
    queryKey: ['users', 'for-manager'],
    queryFn: () => api.get<OrgUser[]>('/api/v1/users?per_page=100'),
    enabled: isAdmin,
  });
  const deps = depsRes?.data ?? [];
  const users = usersRes?.data ?? [];
  const userName = (id: string | null) => users.find((u) => u.id === id)?.full_name ?? '—';

  const reset = () => {
    setForm(EMPTY);
    setEditId(null);
  };

  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: form.name,
        parent_id: form.parent_id || null,
        manager_user_id: form.manager_user_id || null,
      };
      return editId
        ? api.put<Department>(`/api/v1/departments/${editId}`, body)
        : api.post<Department>('/api/v1/departments', body);
    },
    onSuccess: () => {
      setError(null);
      reset();
      queryClient.invalidateQueries({ queryKey: ['departments'] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  const del = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/departments/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['departments'] }),
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  if (!isAdmin) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">Quản trị</h1>
        <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Chỉ chủ sở hữu / quản trị viên mới truy cập được.
        </p>
      </div>
    );
  }

  const startEdit = (d: Department) => {
    setEditId(d.id);
    setForm({
      name: d.name,
      parent_id: d.parent_id ?? '',
      manager_user_id: d.manager_user_id ?? '',
    });
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Quản trị</h1>
      <AdminTabs />

      <form
        className="grid gap-3 rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100 sm:grid-cols-4"
        onSubmit={(e) => {
          e.preventDefault();
          if (form.name.trim()) save.mutate();
        }}
      >
        <div className="sm:col-span-2">
          <label className="mb-1 block text-sm text-gray-500">Tên phòng ban *</label>
          <Input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Phòng CNTT"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-500">Thuộc phòng (cha)</label>
          <select
            value={form.parent_id}
            onChange={(e) => setForm({ ...form, parent_id: e.target.value })}
            className="h-10 w-full rounded-lg border border-gray-300 bg-white px-2 text-sm"
          >
            <option value="">— Cấp cao nhất —</option>
            {deps
              .filter((d) => d.id !== editId)
              .map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm text-gray-500">Trưởng đơn vị</label>
          <select
            value={form.manager_user_id}
            onChange={(e) => setForm({ ...form, manager_user_id: e.target.value })}
            className="h-10 w-full rounded-lg border border-gray-300 bg-white px-2 text-sm"
          >
            <option value="">— Chưa gán —</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name}
              </option>
            ))}
          </select>
        </div>
        {error && (
          <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-4">{error}</p>
        )}
        <div className="flex gap-2 sm:col-span-4">
          <Button type="submit" disabled={save.isPending}>
            {editId ? 'Cập nhật phòng ban' : '+ Thêm phòng ban'}
          </Button>
          {editId && (
            <Button type="button" variant="secondary" onClick={reset}>
              Hủy
            </Button>
          )}
        </div>
      </form>

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-100">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-100 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Phòng ban</th>
              <th className="px-4 py-3">Trưởng đơn vị</th>
              <th className="px-4 py-3">Nhân sự</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {deps.length ? (
              orderTree(deps).map(({ dep, depth }) => (
                <tr key={dep.id} className="hover:bg-gray-50/60">
                  <td className="px-4 py-3 font-medium text-gray-900">
                    <span style={{ paddingLeft: `${depth * 20}px` }}>
                      {depth > 0 ? '└ ' : ''}
                      {dep.name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{userName(dep.manager_user_id)}</td>
                  <td className="px-4 py-3 text-gray-600">{dep.member_count ?? 0}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => startEdit(dep)}
                      className="mr-3 text-sm text-primary-600 hover:underline"
                    >
                      Sửa
                    </button>
                    <button
                      onClick={() => {
                        if (window.confirm(`Xóa phòng "${dep.name}"?`)) del.mutate(dep.id);
                      }}
                      className="text-sm text-red-600 hover:underline"
                    >
                      Xóa
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-gray-400">
                  Chưa có phòng ban — thêm ở trên.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
