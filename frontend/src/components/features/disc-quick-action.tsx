'use client';

// Trạng thái DISC + thao tác nhanh (gửi / gửi lại / xem kết quả).
// Dùng chung ở trang danh sách ứng viên và trang Trắc nghiệm — để DISC dễ tìm, thao tác ngay
// không phải mở từng hồ sơ. Trạng thái suy ra từ pipeline_stage (xem discStatusFromStage).

import { useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { api, ApiError } from '@/lib/api-client';
import { usePerms } from '@/lib/permissions';
import { discStatusFromStage, type Candidate, type TestLink } from '@/lib/types';

export function DiscQuickAction({ candidate }: { candidate: Candidate }) {
  const perms = usePerms();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [testUrl, setTestUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const status = discStatusFromStage(candidate.pipeline_stage);

  const send = useMutation({
    // Backend cho gửi test khi RECEIVED (tự chuyển ASSESSMENT) hoặc ASSESSMENT (gửi lại)
    mutationFn: () => api.post<TestLink>('/api/v1/test-links', { candidate_id: candidate.id }),
    onSuccess: (res) => {
      setError(null);
      setTestUrl(res.data.test_url);
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['candidate', candidate.id] });
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  const copyLink = async () => {
    if (!testUrl) return;
    try {
      await navigator.clipboard.writeText(testUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Trình duyệt có thể chặn clipboard — link vẫn hiện để copy tay
    }
  };

  return (
    <div className="flex flex-col gap-1">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${status.tone}`}>
          {status.label}
        </span>
        {status.hasResult && (
          <Link
            href={`/candidates/${candidate.id}`}
            className="text-xs font-medium text-primary-600 hover:underline"
          >
            Xem →
          </Link>
        )}
        {status.canSend && perms.canRecruit && (
          <Button
            size="sm"
            variant="secondary"
            disabled={send.isPending}
            onClick={() => send.mutate()}
          >
            {send.isPending ? 'Đang gửi…' : status.sendLabel}
          </Button>
        )}
      </div>
      {testUrl && (
        <button
          type="button"
          onClick={copyLink}
          title="Bấm để sao chép link gửi cho ứng viên"
          className="max-w-xs truncate text-left text-xs text-green-700 hover:underline"
        >
          {copied ? '✓ Đã sao chép link' : `Link: ${testUrl}`}
        </button>
      )}
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
