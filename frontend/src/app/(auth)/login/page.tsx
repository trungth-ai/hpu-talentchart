'use client';

// Trang đăng nhập — react-hook-form + zod (Sprint 1)
// Login scoped theo tổ chức: nhập org slug (dev) hoặc tự nhận từ subdomain

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ApiError } from '@/lib/api-client';
import { useAuthStore, type AuthUser } from '@/stores/auth';

const loginSchema = z.object({
  org_slug: z.string().min(1, 'Vui lòng nhập mã tổ chức'),
  email: z.string().email('Email không đúng định dạng'),
  password: z.string().min(1, 'Vui lòng nhập mật khẩu'),
});

type LoginForm = z.infer<typeof loginSchema>;

interface LoginData {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export default function LoginPage() {
  const router = useRouter();
  const { setTokens, setUser } = useAuthStore();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (form: LoginForm) => {
    setServerError(null);
    try {
      // Gọi fetch trực tiếp (không qua api client) để gắn X-Org-Slug —
      // resolve tenant khi chạy trên domain chính; production dùng subdomain
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8003'}/api/v1/auth/login`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Org-Slug': form.org_slug,
          },
          body: JSON.stringify({ email: form.email, password: form.password }),
        }
      );
      const body = await response.json();
      if (!response.ok || body.status === 'error') {
        setServerError(body.message ?? 'Đăng nhập thất bại, vui lòng thử lại');
        return;
      }
      const data = body.data as LoginData;
      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);
      router.replace('/dashboard');
    } catch (err) {
      setServerError(
        err instanceof ApiError ? err.message : 'Không kết nối được máy chủ, vui lòng thử lại'
      );
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-sm ring-1 ring-gray-100">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-primary-700">TalentChart</h1>
          <p className="mt-1 text-sm text-gray-500">
            Đăng nhập vào hệ thống tuyển dụng của tổ chức bạn
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          <div>
            <Label htmlFor="org_slug">Mã tổ chức</Label>
            <Input
              id="org_slug"
              placeholder="vd: hpu"
              autoComplete="organization"
              {...register('org_slug')}
            />
            {errors.org_slug && (
              <p className="mt-1 text-sm text-red-600">{errors.org_slug.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="ban@tochuc.edu.vn"
              autoComplete="email"
              {...register('email')}
            />
            {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
          </div>

          <div>
            <Label htmlFor="password">Mật khẩu</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              {...register('password')}
            />
            {errors.password && (
              <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
            )}
          </div>

          {serverError && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{serverError}</p>
          )}

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Đang đăng nhập…' : 'Đăng nhập'}
          </Button>
        </form>
      </div>
    </div>
  );
}
