'use client';

// Chi tiết đợt tuyển — gộp Tin tuyển dụng + Ứng viên THEO ĐỢT (drill-down từ /recruitment).

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { use, useState } from 'react';

import { CandidateFormModal } from '@/components/features/candidate-form-modal';
import { DiscQuickAction } from '@/components/features/disc-quick-action';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { api, ApiError } from '@/lib/api-client';
import { STAGE_COLORS, STAGE_LABELS, type Campaign, type Candidate, type JobPost } from '@/lib/types';
import { formatVND } from '@/lib/utils';

const EMPTY_JOB = { title: '', location: '', salary_min: '', salary_max: '', description: '' };

export default function CampaignDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();
  const [showJobForm, setShowJobForm] = useState(false);
  const [job, setJob] = useState(EMPTY_JOB);
  const [jobError, setJobError] = useState<string | null>(null);
  const [showAddApplicant, setShowAddApplicant] = useState(false);

  const { data: campaignRes, isLoading } = useQuery({
    queryKey: ['campaign', id],
    queryFn: () => api.get<Campaign>(`/api/v1/campaigns/${id}`),
  });
  const campaign = campaignRes?.data;

  const { data: jobsRes } = useQuery({
    queryKey: ['job-posts', 'by-campaign', id],
    queryFn: () => api.get<JobPost[]>(`/api/v1/job-posts?campaign_id=${id}&per_page=50`),
  });

  const { data: applicantsRes } = useQuery({
    queryKey: ['candidates', 'by-campaign', id],
    queryFn: () =>
      api.get<Candidate[]>(`/api/v1/candidates?campaign_id=${id}&candidate_type=applicant&per_page=50`),
  });

  const updateStatus = useMutation({
    mutationFn: (status: string) => api.put<Campaign>(`/api/v1/campaigns/${id}`, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['campaign', id] }),
  });

  const createJob = useMutation({
    mutationFn: () =>
      api.post<JobPost>('/api/v1/job-posts', {
        title: job.title,
        location: job.location || null,
        salary_min: job.salary_min ? parseInt(job.salary_min, 10) : null,
        salary_max: job.salary_max ? parseInt(job.salary_max, 10) : null,
        description: job.description || null,
        campaign_id: id,
      }),
    onSuccess: () => {
      setShowJobForm(false);
      setJob(EMPTY_JOB);
      setJobError(null);
      queryClient.invalidateQueries({ queryKey: ['job-posts', 'by-campaign', id] });
    },
    onError: (e) => setJobError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra'),
  });

  const togglePublish = useMutation({
    mutationFn: ({ jobId, publish }: { jobId: string; publish: boolean }) =>
      api.post(`/api/v1/job-posts/${jobId}/${publish ? 'publish' : 'unpublish'}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['job-posts', 'by-campaign', id] }),
  });

  if (isLoading || !campaign) {
    return <div className="py-16 text-center text-gray-400">Đang tải…</div>;
  }

  return (
    <div className="space-y-6">
      <Link href="/recruitment" className="text-sm text-primary-600 hover:underline">
        ← Tất cả đợt tuyển
      </Link>

      {/* Header đợt tuyển */}
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
          <p className="text-sm text-gray-500">
            {campaign.position}
            {campaign.department ? ` · ${campaign.department}` : ''} · chỉ tiêu{' '}
            {campaign.target_headcount}
            {campaign.salary_min || campaign.salary_max
              ? ` · ${formatVND(campaign.salary_min)} – ${formatVND(campaign.salary_max)}`
              : ''}
          </p>
        </div>
        <div>
          {campaign.status === 'draft' && (
            <Button size="sm" onClick={() => updateStatus.mutate('open')}>
              Mở đợt tuyển
            </Button>
          )}
          {campaign.status === 'open' && (
            <Button size="sm" variant="secondary" onClick={() => updateStatus.mutate('closed')}>
              Đóng đợt tuyển
            </Button>
          )}
          {campaign.status === 'closed' && (
            <span className="rounded-full bg-red-100 px-3 py-1 text-sm text-red-700">Đã đóng</span>
          )}
        </div>
      </header>

      {/* Tin tuyển dụng của đợt */}
      <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">
            Tin tuyển dụng ({jobsRes?.data?.length ?? 0})
          </h2>
          <Button size="sm" variant="secondary" onClick={() => setShowJobForm((v) => !v)}>
            {showJobForm ? 'Đóng' : '+ Thêm tin'}
          </Button>
        </div>

        {showJobForm && (
          <form
            className="mb-4 grid gap-3 rounded-lg bg-gray-50 p-4 sm:grid-cols-2"
            onSubmit={(e) => {
              e.preventDefault();
              createJob.mutate();
            }}
          >
            <div className="sm:col-span-2">
              <Label htmlFor="j-title">Tiêu đề *</Label>
              <Input
                id="j-title"
                required
                value={job.title}
                onChange={(e) => setJob({ ...job, title: e.target.value })}
                placeholder="Giảng viên Công nghệ thông tin"
              />
            </div>
            <div>
              <Label htmlFor="j-loc">Địa điểm</Label>
              <Input
                id="j-loc"
                value={job.location}
                onChange={(e) => setJob({ ...job, location: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label htmlFor="j-min">Lương từ</Label>
                <Input
                  id="j-min"
                  type="number"
                  min={0}
                  step={500000}
                  value={job.salary_min}
                  onChange={(e) => setJob({ ...job, salary_min: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="j-max">Lương đến</Label>
                <Input
                  id="j-max"
                  type="number"
                  min={0}
                  step={500000}
                  value={job.salary_max}
                  onChange={(e) => setJob({ ...job, salary_max: e.target.value })}
                />
              </div>
            </div>
            <div className="sm:col-span-2">
              <Label htmlFor="j-desc">Mô tả</Label>
              <textarea
                id="j-desc"
                rows={3}
                value={job.description}
                onChange={(e) => setJob({ ...job, description: e.target.value })}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
              />
            </div>
            {jobError && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 sm:col-span-2">
                {jobError}
              </p>
            )}
            <div className="sm:col-span-2">
              <Button type="submit" size="sm" disabled={createJob.isPending}>
                {createJob.isPending ? 'Đang tạo…' : 'Tạo tin (nháp)'}
              </Button>
            </div>
          </form>
        )}

        {jobsRes?.data?.length ? (
          <ul className="divide-y divide-gray-50">
            {jobsRes.data.map((j) => (
              <li key={j.id} className="flex items-center justify-between py-2.5">
                <div>
                  <p className="text-sm font-medium text-gray-900">{j.title}</p>
                  <p className="text-xs text-gray-500">
                    /{j.slug}
                    {j.location ? ` · ${j.location}` : ''}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      j.is_published ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {j.is_published ? 'Đang đăng' : 'Nháp'}
                  </span>
                  <Button
                    size="sm"
                    variant={j.is_published ? 'secondary' : 'primary'}
                    disabled={togglePublish.isPending}
                    onClick={() => togglePublish.mutate({ jobId: j.id, publish: !j.is_published })}
                  >
                    {j.is_published ? 'Gỡ tin' : 'Đăng tin'}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="py-4 text-center text-sm text-gray-400">Chưa có tin tuyển dụng cho đợt này</p>
        )}
      </section>

      {/* Ứng viên của đợt */}
      <section className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-gray-900">
            Ứng viên ({applicantsRes?.data?.length ?? 0})
          </h2>
          <Button size="sm" onClick={() => setShowAddApplicant(true)}>
            + Thêm ứng viên
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-100 text-xs uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-3 py-2">Họ tên</th>
                <th className="px-3 py-2">Trạng thái</th>
                <th className="px-3 py-2">Can Chi</th>
                <th className="px-3 py-2">Cung</th>
                <th className="px-3 py-2">DISC</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {applicantsRes?.data?.length ? (
                applicantsRes.data.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50/60">
                    <td className="px-3 py-2">
                      <Link
                        href={`/candidates/${c.id}`}
                        className="font-medium text-gray-900 hover:text-primary-700"
                      >
                        {c.full_name}
                      </Link>
                      <p className="text-xs text-gray-500">{c.email}</p>
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${STAGE_COLORS[c.pipeline_stage]}`}
                      >
                        {STAGE_LABELS[c.pipeline_stage]}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-700">{c.tuoi_am ?? '—'}</td>
                    <td className="px-3 py-2 text-gray-700">{c.cung_hoang_dao ?? '—'}</td>
                    <td className="px-3 py-2">
                      <DiscQuickAction candidate={c} />
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-gray-400">
                    Chưa có ứng viên trong đợt này
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {showAddApplicant && (
        <CandidateFormModal
          mode="create"
          campaignId={id}
          defaultType="applicant"
          onClose={() => setShowAddApplicant(false)}
        />
      )}
    </div>
  );
}
