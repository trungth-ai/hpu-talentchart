'use client';

// Layout khu vực admin (Sprint 7) — sidebar + header + auth guard
// Mọi trang trong (admin) đều yêu cầu đăng nhập; chưa có token → về /login

import {
  ClipboardCheck,
  LayoutDashboard,
  LogOut,
  type LucideIcon,
  Megaphone,
  Shield,
  Users,
} from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth';

const NAV_ITEMS: { href: string; label: string; icon: LucideIcon; adminOnly?: boolean }[] = [
  { href: '/dashboard', label: 'Tổng quan', icon: LayoutDashboard },
  { href: '/recruitment', label: 'Tuyển dụng', icon: Megaphone },
  { href: '/employees', label: 'Nhân sự', icon: Users },
  { href: '/assessments', label: 'Trắc nghiệm DISC', icon: ClipboardCheck },
  { href: '/admin/users', label: 'Quản trị', icon: Shield, adminOnly: true },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { accessToken, user, logout } = useAuthStore();
  const isAdmin = ['owner', 'admin'].includes(user?.org_role ?? '');
  // Tránh lỗi hydration: store persist chỉ có sau khi mount
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  useEffect(() => {
    if (mounted && !accessToken) router.replace('/login');
  }, [mounted, accessToken, router]);

  if (!mounted || !accessToken) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-400">
        Đang tải…
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-20 flex w-60 flex-col border-r border-gray-200 bg-white">
        <div className="flex h-16 items-center border-b border-gray-100 px-6">
          <Link href="/dashboard" className="text-lg font-bold text-primary-700">
            TalentChart
          </Link>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin).map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                pathname.startsWith(href)
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-gray-100 p-3">
          <div className="mb-2 px-3">
            <p className="truncate text-sm font-medium text-gray-900">{user?.full_name}</p>
            <p className="truncate text-xs text-gray-500">{user?.email}</p>
          </div>
          <button
            onClick={() => {
              logout();
              router.replace('/login');
            }}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <LogOut className="h-4 w-4" />
            Đăng xuất
          </button>
        </div>
      </aside>

      {/* Nội dung chính */}
      <main className="ml-60 flex-1 px-8 py-6">{children}</main>
    </div>
  );
}
