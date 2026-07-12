'use client';

// Tab điều hướng trong khu Quản trị (Người dùng | Cài đặt tổ chức)

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { href: '/admin/users', label: 'Người dùng' },
  { href: '/admin/settings', label: 'Cài đặt tổ chức' },
];

export function AdminTabs() {
  const pathname = usePathname();
  return (
    <div className="flex gap-1 border-b border-gray-200">
      {TABS.map((t) => (
        <Link
          key={t.href}
          href={t.href}
          className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            pathname === t.href
              ? 'border-primary-600 text-primary-700'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}
