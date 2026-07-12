'use client';

// Cài đặt tổ chức — bật/tắt Eastern Layer, domain Google Workspace, auto-provision.
// Đọc: hr_manager+; Sửa (PUT): chỉ owner/admin (backend chốt quyền require_admin).

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { AdminTabs } from '@/components/features/admin-tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api, ApiError } from '@/lib/api-client';
import type { OrganizationInfo } from '@/lib/types';
import { useAuthStore } from '@/stores/auth';

export default function AdminSettingsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const isAdmin = ['owner', 'admin'].includes(user?.org_role ?? '');
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data } = useQuery({
    queryKey: ['organization'],
    queryFn: () => api.get<OrganizationInfo>('/api/v1/organization'),
  });
  const org = data?.data;

  const [eastern, setEastern] = useState(false);
  const [domain, setDomain] = useState('');
  const [autoProvision, setAutoProvision] = useState(false);

  useEffect(() => {
    if (org) {
      setEastern(Boolean(org.settings.eastern_layer_enabled));
      setDomain(String(org.settings.google_workspace_domain ?? ''));
      setAutoProvision(Boolean(org.settings.google_auto_provision));
    }
  }, [org]);

  const save = useMutation({
    mutationFn: () =>
      api.put<OrganizationInfo>('/api/v1/organization/settings', {
        eastern_layer_enabled: eastern,
        google_workspace_domain: domain || null,
        google_auto_provision: autoProvision,
      }),
    onSuccess: () => {
      setError(null);
      setMsg('Đã lưu cài đặt tổ chức');
      queryClient.invalidateQueries({ queryKey: ['organization'] });
      setTimeout(() => setMsg(null), 2000);
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-gray-900">Quản trị</h1>
      <AdminTabs />

      {org && (
        <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
          <p className="text-sm text-gray-500">Tổ chức</p>
          <p className="text-lg font-semibold text-gray-900">{org.name}</p>
          <p className="text-xs text-gray-400">Mã tổ chức (subdomain): {org.slug}</p>
        </div>
      )}

      <form
        className="space-y-4 rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={eastern}
            disabled={!isAdmin}
            onChange={(e) => setEastern(e.target.checked)}
            className="mt-1"
          />
          <span>
            <span className="text-sm font-medium text-gray-900">
              Bật Eastern Layer (tử vi phương Đông)
            </span>
            <span className="block text-xs text-gray-500">
              Hiện thêm Can Chi / Nạp Âm / Mệnh / Tam hợp. Mặc định tắt.
            </span>
          </span>
        </label>

        <div>
          <Label htmlFor="domain">Domain Google Workspace</Label>
          <Input
            id="domain"
            value={domain}
            disabled={!isAdmin}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="hpu.edu.vn"
          />
        </div>

        <label className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={autoProvision}
            disabled={!isAdmin}
            onChange={(e) => setAutoProvision(e.target.checked)}
            className="mt-1"
          />
          <span>
            <span className="text-sm font-medium text-gray-900">
              Tự tạo tài khoản khi đăng nhập Google đúng domain
            </span>
            <span className="block text-xs text-gray-500">
              Người mới đăng nhập bằng email thuộc domain trên sẽ được tạo với vai trò Thành viên.
            </span>
          </span>
        </label>

        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        {msg && <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">{msg}</p>}

        {isAdmin ? (
          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? 'Đang lưu…' : 'Lưu cài đặt'}
          </Button>
        ) : (
          <p className="text-xs text-amber-600">Chỉ quản trị viên mới sửa được cài đặt.</p>
        )}
      </form>
    </div>
  );
}
