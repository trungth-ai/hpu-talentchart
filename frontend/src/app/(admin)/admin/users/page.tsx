'use client';

// Quản trị người dùng — đổi vai trò + khóa/mở (chỉ owner/admin). Backend chốt quyền chặt chẽ:
// không tự sửa mình, không thao tác người quyền ngang/cao hơn, không cấp quyền >= của mình.

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { AdminTabs } from '@/components/features/admin-tabs';
import { Button } from '@/components/ui/button';
import { api, ApiError } from '@/lib/api-client';
import { ORG_ROLE_LABELS, type OrgUser } from '@/lib/types';
import { useAuthStore } from '@/stores/auth';

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const isAdmin = ['owner', 'admin'].includes(user?.org_role ?? '');
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['users', 'admin-list'],
    queryFn: () => api.get<OrgUser[]>('/api/v1/users?include_inactive=true&per_page=100'),
    enabled: isAdmin,
  });

  const patch = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, string> }) =>
      api.patch<OrgUser>(`/api/v1/users/${id}`, body),
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  if (!isAdmin) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">Quản trị</h1>
        <p className="rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Chỉ chủ sở hữu / quản trị viên mới truy cập được khu quản trị.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Quản trị</h1>
      <AdminTabs />

      {error && <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{error}</p>}

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-gray-100">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-gray-100 text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Người dùng</th>
              <th className="px-4 py-3">Vai trò</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3"></th>
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
              data.data.map((u) => {
                const isSelf = u.id === user?.id;
                const locked = u.status !== 'active';
                return (
                  <tr key={u.id} className="hover:bg-gray-50/60">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900">
                        {u.full_name}
                        {isSelf && <span className="ml-2 text-xs text-gray-400">(bạn)</span>}
                      </p>
                      <p className="text-xs text-gray-500">{u.email}</p>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={u.org_role}
                        disabled={isSelf || patch.isPending}
                        onChange={(e) =>
                          patch.mutate({ id: u.id, body: { org_role: e.target.value } })
                        }
                        className="h-9 rounded-lg border border-gray-300 bg-white px-2 text-sm disabled:bg-gray-50 disabled:text-gray-400"
                      >
                        {Object.entries(ORG_ROLE_LABELS).map(([k, v]) => (
                          <option key={k} value={k}>
                            {v}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          locked ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {locked ? 'Đã khóa' : 'Đang hoạt động'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {!isSelf && (
                        <Button
                          size="sm"
                          variant={locked ? 'primary' : 'danger'}
                          disabled={patch.isPending}
                          onClick={() =>
                            patch.mutate({
                              id: u.id,
                              body: { status: locked ? 'active' : 'inactive' },
                            })
                          }
                        >
                          {locked ? 'Mở khóa' : 'Khóa'}
                        </Button>
                      )}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-gray-400">
                  Chưa có người dùng
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-400">
        Chỉ đổi được vai trò / khóa người có quyền thấp hơn bạn. Đăng nhập dùng Google Workspace
        nên không quản lý mật khẩu tại đây.
      </p>
    </div>
  );
}
