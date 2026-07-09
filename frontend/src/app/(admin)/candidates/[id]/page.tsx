'use client';

// Chi tiết ứng viên (Sprint 7): thông tin + chuyển pipeline tuần tự + gửi bài test
// + kết quả DISC + 12 Personality Archetype
// + EPA Eastern Layer (Tử vi phương Đông + So sánh tương hợp) — chỉ hiện khi org bật
//   eastern_layer_enabled (quy tắc hiển thị Critical Business Rules)
// + Sửa / Xóa (soft-delete) hồ sơ

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { use, useState } from 'react';

import { CandidateFormModal } from '@/components/features/candidate-form-modal';
import { Button } from '@/components/ui/button';
import { api, ApiError } from '@/lib/api-client';
import {
  STAGE_COLORS,
  STAGE_LABELS,
  TYPE_LABELS,
  nextStages,
  type AdminTestResult,
  type ArchetypeResult,
  type Candidate,
  type CompatibilityResult,
  type TestLink,
  type TodayCanChi,
  type ZodiacResult,
} from '@/lib/types';
import { formatDate } from '@/lib/utils';

const DISC_NAMES: Record<string, string> = {
  D: 'Quyết đoán (D)',
  I: 'Ảnh hưởng (I)',
  S: 'Kiên định (S)',
  C: 'Chuẩn mực (C)',
};

export default function CandidateDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const [actionError, setActionError] = useState<string | null>(null);
  const [testUrl, setTestUrl] = useState<string | null>(null);
  const [otherId, setOtherId] = useState('');
  const [showEdit, setShowEdit] = useState(false);

  const { data: candidateRes, isLoading } = useQuery({
    queryKey: ['candidate', id],
    queryFn: () => api.get<Candidate>(`/api/v1/candidates/${id}`),
  });
  const candidate = candidateRes?.data;

  const { data: testResult } = useQuery({
    queryKey: ['candidate', id, 'test-result'],
    queryFn: () => api.get<AdminTestResult>(`/api/v1/test-links/candidates/${id}/result`),
    enabled: Boolean(candidate),
    retry: false,
  });

  const { data: archetypeRes } = useQuery({
    queryKey: ['candidate', id, 'archetype'],
    queryFn: () => api.get<ArchetypeResult>(`/api/v1/epa/candidates/${id}/archetype`),
    enabled: Boolean(testResult?.data),
    retry: false,
  });
  const archetype = archetypeRes?.data;

  // Dò Eastern Layer: /epa/today lỗi (422/400) → org chưa bật → ẩn toàn bộ mục Đông phương
  const { data: easternProbe } = useQuery({
    queryKey: ['epa', 'today'],
    queryFn: () => api.get<TodayCanChi>('/api/v1/epa/today'),
    retry: false,
  });
  const easternEnabled = Boolean(easternProbe?.data);

  // Tử vi của chính ứng viên (cần epa_consent + birth_date)
  const { data: zodiacRes, error: zodiacError } = useQuery({
    queryKey: ['candidate', id, 'zodiac'],
    queryFn: () => api.get<ZodiacResult>(`/api/v1/epa/candidates/${id}/zodiac`),
    enabled: Boolean(candidate) && easternEnabled,
    retry: false,
  });

  // Danh sách người để so sánh tương hợp
  const { data: peopleRes } = useQuery({
    queryKey: ['candidates', 'compat-picker'],
    queryFn: () => api.get<Candidate[]>('/api/v1/candidates?per_page=100'),
    enabled: easternEnabled,
  });
  const people = (peopleRes?.data ?? []).filter((p) => p.id !== id);

  const {
    data: compatRes,
    error: compatError,
    isFetching: compatLoading,
  } = useQuery({
    queryKey: ['epa', 'compat', id, otherId],
    queryFn: () =>
      api.get<CompatibilityResult>(
        `/api/v1/epa/compatibility?candidate1_id=${id}&candidate2_id=${otherId}`
      ),
    enabled: easternEnabled && Boolean(otherId),
    retry: false,
  });

  const transition = useMutation({
    mutationFn: (target: string) =>
      api.post<Candidate>(`/api/v1/candidates/${id}/transition`, { target_stage: target }),
    onSuccess: () => {
      setActionError(null);
      queryClient.invalidateQueries({ queryKey: ['candidate', id] });
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
    onError: (e) => setActionError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  const sendTest = useMutation({
    mutationFn: () => api.post<TestLink>('/api/v1/test-links', { candidate_id: id }),
    onSuccess: (res) => {
      setActionError(null);
      setTestUrl(res.data.test_url);
      queryClient.invalidateQueries({ queryKey: ['candidate', id] });
    },
    onError: (e) => setActionError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  const del = useMutation({
    mutationFn: () => api.delete(`/api/v1/candidates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      router.push('/candidates');
    },
    onError: (e) => setActionError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  if (isLoading || !candidate) {
    return <div className="py-16 text-center text-gray-400">Đang tải…</div>;
  }

  const allowedNext = nextStages(candidate.pipeline_stage);

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{candidate.full_name}</h1>
          <p className="text-sm text-gray-500">
            {TYPE_LABELS[candidate.candidate_type]}
            {candidate.employee_code ? ` · ${candidate.employee_code}` : ''}
            {candidate.department ? ` · ${candidate.department}` : ''}
            {candidate.position ? ` · ${candidate.position}` : ''}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span
            className={`rounded-full px-3 py-1 text-sm font-medium ${STAGE_COLORS[candidate.pipeline_stage]}`}
          >
            {STAGE_LABELS[candidate.pipeline_stage]}
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setShowEdit(true)}>
              Sửa
            </Button>
            <Button
              size="sm"
              variant="danger"
              disabled={del.isPending}
              onClick={() => {
                if (window.confirm(`Ẩn (xóa mềm) hồ sơ ${candidate.full_name}?`)) del.mutate();
              }}
            >
              Xóa
            </Button>
          </div>
        </div>
      </header>

      {actionError && (
        <p className="rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">{actionError}</p>
      )}
      {testUrl && (
        <p className="break-all rounded-lg bg-green-50 px-4 py-2 text-sm text-green-800">
          Đã tạo link bài test — gửi cho ứng viên: <b>{testUrl}</b>
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Cột trái: thông tin + hành động */}
        <div className="space-y-6">
          <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <h2 className="mb-3 font-semibold text-gray-900">Thông tin liên hệ</h2>
            <dl className="space-y-2 text-sm">
              <div>
                <dt className="text-gray-500">Email</dt>
                <dd className="font-medium text-gray-900">{candidate.email}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Điện thoại</dt>
                <dd className="font-medium text-gray-900">{candidate.phone ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Nguồn</dt>
                <dd className="text-gray-700">{candidate.source ?? '—'}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Đồng ý dữ liệu EPA</dt>
                <dd className="text-gray-700">
                  {candidate.epa_consent ? '✓ Đã đồng ý (opt-in)' : 'Chưa đồng ý'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Ngày tạo</dt>
                <dd className="text-gray-700">{formatDate(candidate.created_at)}</dd>
              </div>
            </dl>
          </section>

          <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <h2 className="mb-3 font-semibold text-gray-900">Hành động</h2>
            <div className="space-y-2">
              {allowedNext.map((stage) => (
                <Button
                  key={stage}
                  className="w-full"
                  variant={stage === 'REJECTED' ? 'danger' : 'primary'}
                  disabled={transition.isPending}
                  onClick={() => transition.mutate(stage)}
                >
                  Chuyển sang: {STAGE_LABELS[stage]}
                </Button>
              ))}
              {['SCREENING', 'TEST_SENT'].includes(candidate.pipeline_stage) && (
                <Button
                  variant="secondary"
                  className="w-full"
                  disabled={sendTest.isPending}
                  onClick={() => sendTest.mutate()}
                >
                  {candidate.pipeline_stage === 'TEST_SENT'
                    ? 'Gửi lại link bài test'
                    : 'Gửi bài test DISC'}
                </Button>
              )}
              {allowedNext.length === 0 && (
                <p className="text-center text-sm text-gray-400">
                  Hồ sơ đã ở trạng thái kết thúc
                </p>
              )}
            </div>
            <p className="mt-3 text-xs text-gray-400">
              Pipeline chỉ đi tuần tự theo quy trình — không thể nhảy cóc trạng thái.
            </p>
          </section>
        </div>

        {/* Cột phải: kết quả test + archetype + Đông phương */}
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
            <h2 className="mb-3 font-semibold text-gray-900">Kết quả bài test DISC</h2>
            {testResult?.data ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="rounded-xl bg-primary-50 px-4 py-2 text-center">
                    <p className="text-xs text-primary-600">Profile</p>
                    <p className="text-2xl font-bold text-primary-700">
                      {testResult.data.disc_profile}
                    </p>
                  </div>
                  <div className="flex-1 space-y-2">
                    {(['D', 'I', 'S', 'C'] as const).map((d) => (
                      <div key={d} className="flex items-center gap-2">
                        <span className="w-32 text-xs text-gray-500">{DISC_NAMES[d]}</span>
                        <div className="h-2 flex-1 rounded-full bg-gray-100">
                          <div
                            className="h-2 rounded-full bg-primary-500"
                            style={{ width: `${testResult.data.disc_scores[d] ?? 0}%` }}
                          />
                        </div>
                        <span className="w-9 text-right text-xs text-gray-600">
                          {testResult.data.disc_scores[d] ?? 0}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                {testResult.data.analysis?.recommendation_text && (
                  <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                    {testResult.data.analysis.recommendation_text}
                    <span className="mt-1 block text-xs text-amber-600">
                      ⚠ Chỉ là tín hiệu tham khảo — không dùng làm yếu tố quyết định duy nhất.
                    </span>
                  </p>
                )}
                {testResult.data.ai_suggestions?.suggested_questions?.length ? (
                  <details className="text-sm">
                    <summary className="cursor-pointer font-medium text-gray-700">
                      Gợi ý câu hỏi phỏng vấn (
                      {testResult.data.ai_suggestions.suggested_questions.length})
                    </summary>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-gray-600">
                      {testResult.data.ai_suggestions.suggested_questions.map((q) => (
                        <li key={q}>{q}</li>
                      ))}
                    </ul>
                  </details>
                ) : null}
              </div>
            ) : (
              <p className="py-4 text-center text-sm text-gray-400">
                Chưa có kết quả — gửi bài test khi hồ sơ ở bước Sàng lọc
              </p>
            )}
          </section>

          {archetype && (
            <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-gray-900">Personality Archetype</h2>
                <div className="flex items-center gap-2">
                  {archetype.used_eastern_data && (
                    <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700">
                      ☯ Có dùng dữ liệu Đông phương
                    </span>
                  )}
                  <span className="rounded-full bg-primary-100 px-3 py-1 text-sm font-semibold text-primary-700">
                    {archetype.archetype.name_vi}
                  </span>
                </div>
              </div>
              <p className="mb-3 text-sm italic text-gray-500">
                “{archetype.archetype.tagline}”
              </p>
              <p className="text-sm leading-relaxed text-gray-700">{archetype.narrative}</p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <h3 className="mb-1 text-xs font-semibold uppercase text-green-600">
                    Điểm mạnh
                  </h3>
                  <ul className="list-disc space-y-1 pl-4 text-sm text-gray-600">
                    {archetype.archetype.strengths.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3 className="mb-1 text-xs font-semibold uppercase text-amber-600">
                    Cần lưu ý
                  </h3>
                  <ul className="list-disc space-y-1 pl-4 text-sm text-gray-600">
                    {archetype.archetype.watchouts.map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <p className="mt-4 text-xs text-gray-400">{archetype.disclaimer}</p>
            </section>
          )}

          {/* ─── EPA Eastern Layer: chỉ hiện khi tổ chức bật eastern_layer_enabled ─── */}
          {easternEnabled && (
            <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
              <h2 className="mb-3 font-semibold text-gray-900">Tử vi phương Đông</h2>
              {zodiacRes?.data ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{zodiacRes.data.zodiac.emoji}</span>
                    <div>
                      <p className="text-lg font-bold text-gray-900">
                        {zodiacRes.data.zodiac.tuoi_am}
                      </p>
                      <p className="text-sm text-gray-500">
                        Tuổi {zodiacRes.data.zodiac.con_giap}
                      </p>
                    </div>
                  </div>
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <div>
                      <dt className="text-gray-500">Mệnh</dt>
                      <dd className="font-medium text-gray-900">{zodiacRes.data.zodiac.menh}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Nạp Âm</dt>
                      <dd className="font-medium text-gray-900">{zodiacRes.data.zodiac.nap_am}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Thiên Can</dt>
                      <dd className="text-gray-700">{zodiacRes.data.zodiac.thien_can}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Địa Chi</dt>
                      <dd className="text-gray-700">{zodiacRes.data.zodiac.dia_chi}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Năm âm lịch</dt>
                      <dd className="text-gray-700">{zodiacRes.data.zodiac.lunar_year}</dd>
                    </div>
                  </dl>
                  <p className="text-xs text-gray-400">{zodiacRes.data.disclaimer}</p>
                </div>
              ) : (
                <p className="py-3 text-sm text-gray-400">
                  {zodiacError instanceof ApiError
                    ? zodiacError.message
                    : 'Chưa có dữ liệu tử vi (cần ngày sinh + đồng ý dùng dữ liệu EPA).'}
                </p>
              )}
            </section>
          )}

          {easternEnabled && (
            <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
              <h2 className="mb-1 font-semibold text-gray-900">So sánh tương hợp</h2>
              <p className="mb-3 text-sm text-gray-500">
                Chọn người khác để xem độ tương hợp với {candidate.full_name} (theo tam hợp/xung).
              </p>
              <select
                className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none"
                value={otherId}
                onChange={(e) => setOtherId(e.target.value)}
              >
                <option value="">— Chọn người để so sánh —</option>
                {people.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.full_name}
                    {p.department ? ` · ${p.department}` : ''}
                  </option>
                ))}
              </select>

              {otherId && compatLoading && (
                <p className="mt-3 text-sm text-gray-400">Đang tính…</p>
              )}
              {otherId && !compatLoading && compatError instanceof ApiError && (
                <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  {compatError.message}
                </p>
              )}
              {compatRes?.data && (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center gap-4">
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary-50 text-2xl font-bold text-primary-700">
                      {compatRes.data.score}
                    </div>
                    <div className="text-sm text-gray-600">
                      <p>
                        <b>{compatRes.data.person1.full_name}</b> ·{' '}
                        {compatRes.data.person1.zodiac.con_giap}
                      </p>
                      <p>
                        <b>{compatRes.data.person2.full_name}</b> ·{' '}
                        {compatRes.data.person2.zodiac.con_giap}
                      </p>
                    </div>
                  </div>
                  {compatRes.data.notes.length > 0 && (
                    <ul className="list-disc space-y-1 pl-5 text-sm text-gray-700">
                      {compatRes.data.notes.map((n) => (
                        <li key={n}>{n}</li>
                      ))}
                    </ul>
                  )}
                  <p className="text-xs text-gray-400">{compatRes.data.disclaimer}</p>
                </div>
              )}
            </section>
          )}
        </div>
      </div>

      {showEdit && (
        <CandidateFormModal mode="edit" initial={candidate} onClose={() => setShowEdit(false)} />
      )}
    </div>
  );
}
