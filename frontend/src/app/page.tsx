// Trang gốc — điều hướng theo trạng thái đăng nhập (xử lý phía client vì token ở localStorage)
'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/auth';

export default function HomePage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    router.replace(accessToken ? '/dashboard' : '/login');
  }, [accessToken, router]);

  return (
    <div className="flex min-h-screen items-center justify-center text-gray-500">
      Đang chuyển hướng…
    </div>
  );
}
