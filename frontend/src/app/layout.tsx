// Root layout — locale tiếng Việt
import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'TalentChart — Tuyển dụng & Đánh giá nhân sự',
  description:
    'Nền tảng SaaS tuyển dụng và đánh giá nhân sự tích hợp Eastern Personality Assessment',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
