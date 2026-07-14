// Phân quyền phía UI (ẩn nút không dùng được) — backend vẫn là nơi chốt quyền thật (403).
// Bậc: owner 50 > admin 40 > hr_manager 30 > recruiter 20 > member 10.

import { useAuthStore } from '@/stores/auth';

const LEVEL: Record<string, number> = {
  owner: 50,
  admin: 40,
  hr_manager: 30,
  recruiter: 20,
  member: 10,
};

export function roleLevel(role: string | undefined | null): number {
  return LEVEL[role ?? ''] ?? 0;
}

export interface Perms {
  level: number;
  isAdmin: boolean; // >=40: quản trị user/cài đặt/cơ cấu tổ chức
  canManageEmployees: boolean; // >=30 (HR+): thêm/sửa hồ sơ Nhân sự
  canDelete: boolean; // >=30 (HR+): xóa hồ sơ/đợt/tin
  canRecruit: boolean; // >=20: tạo/sửa ứng viên, đợt, tin, gửi DISC
  canView: boolean; // >=10: xem
}

export function permsFor(role: string | undefined | null): Perms {
  const level = roleLevel(role);
  return {
    level,
    isAdmin: level >= 40,
    canManageEmployees: level >= 30,
    canDelete: level >= 30,
    canRecruit: level >= 20,
    canView: level >= 10,
  };
}

export function usePerms(): Perms {
  const { user } = useAuthStore();
  return permsFor(user?.org_role);
}
