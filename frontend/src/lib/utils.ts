// Utils chung — cn() cho Tailwind, format tiền/ngày theo chuẩn HPU
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// Money Integer VNĐ → "15.000.000 đ" (rules/money-integer.md)
export function formatVND(amount: number | null | undefined): string {
  if (amount == null) return 'Thỏa thuận';
  return new Intl.NumberFormat('vi-VN').format(amount) + ' đ';
}

// Ngày lưu YYYY-MM-DD → hiển thị DD/MM/YYYY
export function formatDate(isoDate: string | null | undefined): string {
  if (!isoDate) return '—';
  const [year, month, day] = isoDate.slice(0, 10).split('-');
  return `${day}/${month}/${year}`;
}
