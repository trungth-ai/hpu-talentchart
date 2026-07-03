// Career Page công khai theo tenant (Sprint 4) — Server Component
// URL thật: {slug}.talentchart.hpu.edu.vn (middleware rewrite về đây)

import { formatVND } from '@/lib/utils';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8003';

interface PublicJob {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
}

async function fetchJobs(slug: string): Promise<PublicJob[]> {
  try {
    // Dev: dùng X-Org-Slug; production subdomain tự resolve qua Host header
    const res = await fetch(`${API_URL}/api/v1/public/jobs`, {
      headers: { 'X-Org-Slug': slug },
      next: { revalidate: 60 }, // cache 60s
    });
    if (!res.ok) return [];
    const body = await res.json();
    return body.data ?? [];
  } catch {
    return [];
  }
}

function salaryText(job: PublicJob): string {
  if (job.salary_min == null && job.salary_max == null) return 'Thỏa thuận';
  if (job.salary_min != null && job.salary_max != null) {
    return `${formatVND(job.salary_min)} – ${formatVND(job.salary_max)}`;
  }
  return formatVND(job.salary_min ?? job.salary_max);
}

export default async function CareerPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const jobs = await fetchJobs(slug);

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <header className="mb-10 text-center">
        <h1 className="text-3xl font-bold text-primary-700">Cơ hội nghề nghiệp</h1>
        <p className="mt-2 text-gray-500">
          Các vị trí đang tuyển dụng — ứng tuyển ngay hôm nay
        </p>
      </header>

      {jobs.length === 0 ? (
        <p className="text-center text-gray-500">
          Hiện chưa có vị trí nào đang tuyển. Vui lòng quay lại sau!
        </p>
      ) : (
        <ul className="space-y-4">
          {jobs.map((job) => (
            <li
              key={job.id}
              className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-gray-100"
            >
              <h2 className="text-lg font-semibold text-gray-900">{job.title}</h2>
              <p className="mt-1 text-sm text-gray-500">
                {job.location ?? 'Địa điểm linh hoạt'} · {salaryText(job)}
              </p>
              {job.description && (
                <p className="mt-3 line-clamp-3 text-sm text-gray-600">{job.description}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
