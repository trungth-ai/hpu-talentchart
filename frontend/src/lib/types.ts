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
  gender: 'male' | 'female' | null;
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

// ─── EPA Eastern Layer (Can Chi/Nạp Âm/Mệnh) — chỉ khi org bật eastern_layer_enabled ───
export interface ZodiacInfo {
  thien_can: string;
  dia_chi: string;
  con_giap: string;
  emoji: string;
  tuoi_am: string;
  nap_am: string;
  menh: string;
  lunar_year: number;
  lunar_month: number;
  lunar_day: number;
}

export interface ZodiacResult {
  candidate_id: string;
  full_name: string;
  zodiac: ZodiacInfo;
  disclaimer: string;
}

export interface CompatibilityResult {
  person1: { id: string; full_name: string; gender: string | null; zodiac: ZodiacInfo };
  person2: { id: string; full_name: string; gender: string | null; zodiac: ZodiacInfo };
  score: number;
  relationship: { name: string; description: string }; // quan hệ tuổi trung tính giới
  notes: string[];
  detail: string | null; // mô tả hôn nhân từ sách (chỉ cặp nam–nữ)
  detail_note: string | null;
  disclaimer: string;
}

// Tính cách đặc trưng theo ngày sinh — cung hoàng đạo (2.4)
export interface HoroscopeSign {
  code: string;
  name: string;
  name_book: string;
  emoji: string;
  date_range: string;
  element: string;
  ruling_planet: string;
  lucky_colors: string[];
  personality: string;
  strengths: string[];
  weaknesses: string[];
  careers: string[];
}

export interface ZodiacAnimal {
  dia_chi: string;
  animal: string;
  personality: string;
  strengths: string[];
  weaknesses: string[];
  careers: string[];
}

export interface PersonalityResult {
  candidate_id: string;
  full_name: string;
  horoscope: HoroscopeSign;
  zodiac_summary: { con_giap: string; emoji: string; tuoi_am: string; menh: string };
  zodiac_personality: ZodiacAnimal | null;
  disclaimer: string;
}

// Nhịp sinh học (Biorhythm)
export interface BiorhythmPoint {
  offset: number;
  date: string;
  physical: number;
  emotional: number;
  intellectual: number;
}

export interface BiorhythmResult {
  candidate_id: string;
  full_name: string;
  date: string;
  days_alive: number;
  today: { physical: number; emotional: number; intellectual: number };
  series: BiorhythmPoint[];
  disclaimer: string;
}

// Vận trình ngày/tháng (2.1/2.2)
export interface FortuneResult {
  candidate_id: string;
  full_name: string;
  birth: { day: number; month: number; year: number };
  day: {
    canchi: { solar_date: string; lunar_date: string; day_canchi: string; year_canchi: string };
    narrative: string;
  };
  month: { month: number; year: number; narrative: string; book_guidance: string | null };
  ai_generated: boolean;
  disclaimer: string;
}

export interface LichngaytotBlock {
  url: string;
  excerpt: string;
}
export interface LichngaytotResult {
  date: string; // ngày (YYYY-MM-DD) của nội dung tử vi
  day: LichngaytotBlock | null; // ngày tốt/xấu, sao, giờ hoàng đạo
  zodiac_day: LichngaytotBlock | null; // tử vi theo tuổi
  horoscope_day: LichngaytotBlock | null; // tử vi theo cung
  disclaimer: string;
}

// Nội dung tử vi đầy đủ (Xem thêm) — content tùy kind:
//   zodiac    → { full }
//   horoscope → { book1, tuvitay }
export interface AstrologyRef {
  kind: 'zodiac' | 'horoscope';
  key: string;
  title: string;
  content: Record<string, string>;
  disclaimer: string;
}

// Thống kê nhân sự theo 12 con giáp (dashboard)
export interface ZodiacStatsResult {
  total: number;
  by_zodiac: { dia_chi: string; animal: string; count: number }[];
}

// Can Chi hôm nay (dashboard) — dùng để dò Eastern Layer có bật không
export interface TodayCanChi {
  lunar_date: string;
  year_canchi: string;
  day_canchi: string;
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

// Bước tiếp theo hợp lệ — khớp candidate_service backend (ADR-007):
// đi tiến 1 bước kế, hoặc Từ chối (REJECTED) ở bất kỳ bước chưa kết thúc.
export function nextStages(current: string): string[] {
  const seq = ['NEW', 'SCREENING', 'TEST_SENT', 'TEST_DONE', 'INTERVIEW', 'DECISION'];
  if (current === 'DECISION') return ['HIRED', 'REJECTED'];
  const idx = seq.indexOf(current);
  if (idx < 0) return []; // trạng thái kết thúc (HIRED/REJECTED) hoặc không xác định
  return [seq[idx + 1], 'REJECTED'];
}

// ─── Trạng thái DISC suy ra từ pipeline_stage (dùng ở danh sách + trang Trắc nghiệm) ───
// Không cần gọi thêm API: TEST_SENT = đã gửi link, từ TEST_DONE trở đi = đã có kết quả.
export interface DiscStatus {
  label: string; // nhãn trạng thái hiển thị
  tone: string; // class màu cho badge
  canSend: boolean; // có thể gửi / gửi lại link test
  sendLabel: string; // nhãn nút gửi (rỗng khi không gửi được)
  hasResult: boolean; // đã có kết quả DISC để xem
}

export function discStatusFromStage(stage: string): DiscStatus {
  switch (stage) {
    case 'NEW':
      return {
        label: 'Chưa test',
        tone: 'bg-gray-100 text-gray-600',
        canSend: true,
        sendLabel: 'Sàng lọc & gửi test',
        hasResult: false,
      };
    case 'SCREENING':
      return {
        label: 'Chưa gửi',
        tone: 'bg-blue-100 text-blue-700',
        canSend: true,
        sendLabel: 'Gửi test',
        hasResult: false,
      };
    case 'TEST_SENT':
      return {
        label: 'Đã gửi · chờ làm',
        tone: 'bg-amber-100 text-amber-700',
        canSend: true,
        sendLabel: 'Gửi lại',
        hasResult: false,
      };
    case 'TEST_DONE':
    case 'INTERVIEW':
    case 'DECISION':
    case 'HIRED':
      return {
        label: 'Có kết quả',
        tone: 'bg-green-100 text-green-700',
        canSend: false,
        sendLabel: '',
        hasResult: true,
      };
    case 'REJECTED':
      return {
        label: 'Đã từ chối',
        tone: 'bg-red-100 text-red-700',
        canSend: false,
        sendLabel: '',
        hasResult: false,
      };
    default:
      return {
        label: '—',
        tone: 'bg-gray-100 text-gray-500',
        canSend: false,
        sendLabel: '',
        hasResult: false,
      };
  }
}
