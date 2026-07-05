// Types dùng chung cho API responses (khớp schemas backend)

export interface Candidate {
  id: string;
  full_name: string;
  email: string;
  phone: string | null;
  candidate_type: 'applicant' | 'employee' | 'student' | 'alumni';
  pipeline_stage: string;
  position: string | null;
  source: string | null;
  notes: string | null;
  campaign_id: string | null;
  employee_code: string | null;
  department: string | null;
  epa_consent: boolean;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  position: string;
  department: string | null;
  description: string | null;
  start_date: string | null;
  end_date: string | null;
  target_headcount: number;
  salary_min: number | null;
  salary_max: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface JobPost {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  requirements: string | null;
  benefits: string | null;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  campaign_id: string | null;
  is_published: boolean;
  published_at: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface TestLink {
  id: string;
  candidate_id: string;
  token: string;
  test_url: string;
  expires_at: string;
  is_used: boolean;
  completed_at: string | null;
  created_at: string;
}

export interface AdminTestResult {
  disc_scores: Record<string, number>;
  disc_primary: string;
  disc_secondary: string;
  disc_profile: string;
  personality_scores: Record<string, number>;
  analysis: {
    recommendation_text?: string;
    overall_score?: number;
    fit_score?: number;
    strong_categories?: { key: string; score: number }[];
    weak_categories?: { key: string; score: number }[];
  } | null;
  ai_suggestions: {
    focus_areas?: string[];
    suggested_questions?: string[];
    red_flags_to_watch?: string[];
    behavioral_patterns?: string[];
  } | null;
  overall_score: number | null;
  recommendation: string | null;
  completed_at: string | null;
}

export interface ArchetypeInfo {
  code: string;
  name_en: string;
  name_vi: string;
  tagline: string;
  description: string;
  strengths: string[];
  watchouts: string[];
  communication_dos: string[];
  communication_donts: string[];
  motivations: string[];
  stress_behavior: string[];
  improvement_tips: string[];
  university_fit: string;
}

export interface ArchetypeResult {
  candidate_id: string;
  full_name: string;
  disc_profile: string;
  disc_scores: Record<string, number>;
  archetype: ArchetypeInfo;
  narrative: string;
  used_eastern_data: boolean;
  disclaimer: string;
}

// Pipeline — khớp Critical Business Rules (7 trạng thái tuần tự)
export const PIPELINE_STAGES = [
  'NEW',
  'SCREENING',
  'TEST_SENT',
  'TEST_DONE',
  'INTERVIEW',
  'DECISION',
  'HIRED',
  'REJECTED',
] as const;

export const STAGE_LABELS: Record<string, string> = {
  NEW: 'Mới',
  SCREENING: 'Sàng lọc',
  TEST_SENT: 'Đã gửi test',
  TEST_DONE: 'Xong test',
  INTERVIEW: 'Phỏng vấn',
  DECISION: 'Chờ quyết định',
  HIRED: 'Đã tuyển',
  REJECTED: 'Từ chối',
};

export const STAGE_COLORS: Record<string, string> = {
  NEW: 'bg-gray-100 text-gray-700',
  SCREENING: 'bg-blue-100 text-blue-700',
  TEST_SENT: 'bg-amber-100 text-amber-700',
  TEST_DONE: 'bg-cyan-100 text-cyan-700',
  INTERVIEW: 'bg-purple-100 text-purple-700',
  DECISION: 'bg-orange-100 text-orange-700',
  HIRED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
};

export const TYPE_LABELS: Record<string, string> = {
  applicant: 'Ứng viên',
  employee: 'Nhân sự',
  student: 'Sinh viên',
  alumni: 'Cựu SV',
};

// Bước tiếp theo hợp lệ (tuần tự — khớp candidate_service backend)
export function nextStages(current: string): string[] {
  const seq = ['NEW', 'SCREENING', 'TEST_SENT', 'TEST_DONE', 'INTERVIEW', 'DECISION'];
  if (current === 'DECISION') return ['HIRED', 'REJECTED'];
  const idx = seq.indexOf(current);
  if (idx < 0 || idx === seq.length - 1) return [];
  return [seq[idx + 1]];
}
