'use client';

// Trang làm bài test DISC (port UX từ SmartHire)
// Phần 1: 40 câu DISC — mỗi câu chọn "Giống tôi NHẤT" và "ÍT giống tôi nhất"
// Phần 2: 30 câu tính cách — Likert 1-5
// Nộp bài → hiển thị kết quả Behavioural Layer (DISC profile)

import { use, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8003';

interface TestData {
  candidate_name: string;
  position: string | null;
  disc_questions: { options: { t: string }[] }[];
  personality_categories: { name: string; icon: string; key: string; qs: string[] }[];
}

interface TestResult {
  disc_scores: Record<string, number>;
  disc_primary: string;
  disc_profile: string;
}

type DiscAnswer = { most?: number; least?: number };

const LIKERT_LABELS = ['Hoàn toàn không đúng', 'Không đúng', 'Trung lập', 'Đúng', 'Hoàn toàn đúng'];
const DISC_NAMES: Record<string, string> = {
  D: 'Dominance — Quyết đoán',
  I: 'Influence — Ảnh hưởng',
  S: 'Steadiness — Ổn định',
  C: 'Conscientiousness — Chuẩn mực',
};

export default function TestPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  // Header X-Org-Slug cho dev (production dùng subdomain thật)
  const orgSlug =
    typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get('org')
      : null;

  const [test, setTest] = useState<TestData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [phase, setPhase] = useState<'disc' | 'personality' | 'done'>('disc');
  const [discAnswers, setDiscAnswers] = useState<Record<string, DiscAnswer>>({});
  const [personalityAnswers, setPersonalityAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<TestResult | null>(null);

  useEffect(() => {
    const headers: Record<string, string> = {};
    if (orgSlug) headers['X-Org-Slug'] = orgSlug;
    fetch(`${API_URL}/api/v1/public/test/${token}`, { headers })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok || body.status === 'error') {
          setLoadError(body.message ?? 'Không tải được bài test');
        } else {
          setTest(body.data);
        }
      })
      .catch(() => setLoadError('Không kết nối được máy chủ, vui lòng thử lại'));
  }, [token, orgSlug]);

  if (loadError) {
    return (
      <div className="flex min-h-screen items-center justify-center px-4">
        <p className="rounded-xl bg-red-50 px-6 py-4 text-red-700">{loadError}</p>
      </div>
    );
  }
  if (!test) {
    return (
      <div className="flex min-h-screen items-center justify-center text-gray-500">
        Đang tải bài test…
      </div>
    );
  }

  const discDone = Object.keys(discAnswers).filter(
    (k) => discAnswers[k].most != null && discAnswers[k].least != null
  ).length;
  const totalPersonalityQs = test.personality_categories.reduce(
    (sum, c) => sum + c.qs.length,
    0
  );
  const personalityDone = Object.keys(personalityAnswers).length;

  const setDisc = (qi: number, field: 'most' | 'least', value: number) => {
    setDiscAnswers((prev) => {
      const current = { ...(prev[String(qi)] ?? {}) };
      // Không cho most và least trùng nhau
      if (field === 'most' && current.least === value) delete current.least;
      if (field === 'least' && current.most === value) delete current.most;
      current[field] = value;
      return { ...prev, [String(qi)]: current };
    });
  };

  const submit = async () => {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (orgSlug) headers['X-Org-Slug'] = orgSlug;
      const res = await fetch(`${API_URL}/api/v1/public/test/${token}/submit`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          disc_answers: discAnswers,
          personality_answers: personalityAnswers,
        }),
      });
      const body = await res.json();
      if (!res.ok || body.status === 'error') {
        setSubmitError(body.message ?? 'Nộp bài thất bại, vui lòng thử lại');
      } else {
        setResult(body.data);
        setPhase('done');
        window.scrollTo(0, 0);
      }
    } catch {
      setSubmitError('Không kết nối được máy chủ, vui lòng thử lại');
    } finally {
      setSubmitting(false);
    }
  };

  // ─── Màn hình kết quả ───
  if (phase === 'done' && result) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12">
        <div className="rounded-2xl bg-white p-8 text-center shadow-sm ring-1 ring-gray-100">
          <h1 className="text-2xl font-bold text-primary-700">Hoàn thành bài test!</h1>
          <p className="mt-2 text-gray-500">
            Cảm ơn {test.candidate_name}. Kết quả đã được gửi tới phòng nhân sự.
          </p>
          <div className="mt-8">
            <p className="text-sm uppercase tracking-wide text-gray-400">Nhóm tính cách của bạn</p>
            <p className="mt-1 text-4xl font-bold text-primary-600">{result.disc_profile}</p>
            <p className="mt-1 text-gray-600">{DISC_NAMES[result.disc_primary]}</p>
          </div>
          <div className="mt-8 space-y-3 text-left">
            {(['D', 'I', 'S', 'C'] as const).map((d) => (
              <div key={d}>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium">{DISC_NAMES[d]}</span>
                  <span>{result.disc_scores[d] ?? 0}%</span>
                </div>
                <div className="h-2 rounded-full bg-gray-100">
                  <div
                    className="h-2 rounded-full bg-primary-500"
                    style={{ width: `${result.disc_scores[d] ?? 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-xl font-bold text-primary-700">Bài đánh giá tính cách</h1>
        <p className="text-sm text-gray-500">
          Xin chào <span className="font-medium">{test.candidate_name}</span>
          {test.position ? ` — vị trí ${test.position}` : ''}. Không có câu trả lời
          đúng/sai, hãy chọn theo đúng con người bạn.
        </p>
        <div className="mt-4 h-2 rounded-full bg-gray-100">
          <div
            className="h-2 rounded-full bg-primary-500 transition-all"
            style={{
              width: `${
                phase === 'disc'
                  ? (discDone / test.disc_questions.length) * 50
                  : 50 + (personalityDone / totalPersonalityQs) * 50
              }%`,
            }}
          />
        </div>
      </header>

      {phase === 'disc' && (
        <section className="space-y-6">
          <p className="text-sm font-medium text-gray-700">
            Phần 1/2 — Với mỗi nhóm, chọn 1 câu <b>GIỐNG bạn nhất</b> và 1 câu{' '}
            <b>ÍT giống bạn nhất</b> ({discDone}/{test.disc_questions.length})
          </p>
          {test.disc_questions.map((q, qi) => (
            <div key={qi} className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
              <div className="mb-3 flex justify-between text-xs font-medium text-gray-400">
                <span>Câu {qi + 1}</span>
                <span className="w-32 text-center">Giống nhất / Ít nhất</span>
              </div>
              <div className="space-y-2">
                {q.options.map((opt, oi) => {
                  const ans = discAnswers[String(qi)] ?? {};
                  return (
                    <div key={oi} className="flex items-center gap-3">
                      <p className="flex-1 text-sm text-gray-700">{opt.t}</p>
                      <div className="flex w-32 justify-center gap-2">
                        <button
                          type="button"
                          aria-label={`Câu ${qi + 1} — giống nhất: lựa chọn ${oi + 1}`}
                          onClick={() => setDisc(qi, 'most', oi)}
                          className={cn(
                            'h-7 w-12 rounded-full border text-xs font-medium transition-colors',
                            ans.most === oi
                              ? 'border-green-600 bg-green-600 text-white'
                              : 'border-gray-300 text-gray-400 hover:border-green-400'
                          )}
                        >
                          Nhất
                        </button>
                        <button
                          type="button"
                          aria-label={`Câu ${qi + 1} — ít giống nhất: lựa chọn ${oi + 1}`}
                          onClick={() => setDisc(qi, 'least', oi)}
                          className={cn(
                            'h-7 w-12 rounded-full border text-xs font-medium transition-colors',
                            ans.least === oi
                              ? 'border-red-500 bg-red-500 text-white'
                              : 'border-gray-300 text-gray-400 hover:border-red-300'
                          )}
                        >
                          Ít
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
          <Button
            className="w-full"
            disabled={discDone < test.disc_questions.length}
            onClick={() => {
              setPhase('personality');
              window.scrollTo(0, 0);
            }}
          >
            {discDone < test.disc_questions.length
              ? `Trả lời đủ ${test.disc_questions.length} câu để tiếp tục (còn ${
                  test.disc_questions.length - discDone
                })`
              : 'Tiếp tục phần 2 →'}
          </Button>
        </section>
      )}

      {phase === 'personality' && (
        <section className="space-y-6">
          <p className="text-sm font-medium text-gray-700">
            Phần 2/2 — Mức độ đúng với bạn ({personalityDone}/{totalPersonalityQs})
          </p>
          {(() => {
            let qIndex = -1;
            return test.personality_categories.map((cat) => (
              <div key={cat.key} className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-gray-100">
                <h3 className="mb-3 font-semibold text-gray-800">
                  {cat.icon} {cat.name}
                </h3>
                <div className="space-y-4">
                  {cat.qs.map((question) => {
                    qIndex += 1;
                    const idx = String(qIndex);
                    return (
                      <div key={idx}>
                        <p className="mb-2 text-sm text-gray-700">{question}</p>
                        <div className="flex gap-2">
                          {[1, 2, 3, 4, 5].map((v) => (
                            <button
                              key={v}
                              type="button"
                              title={LIKERT_LABELS[v - 1]}
                              onClick={() =>
                                setPersonalityAnswers((prev) => ({ ...prev, [idx]: v }))
                              }
                              className={cn(
                                'h-9 flex-1 rounded-lg border text-sm font-medium transition-colors',
                                personalityAnswers[idx] === v
                                  ? 'border-primary-600 bg-primary-600 text-white'
                                  : 'border-gray-300 text-gray-500 hover:border-primary-400'
                              )}
                            >
                              {v}
                            </button>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ));
          })()}

          {submitError && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</p>
          )}
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setPhase('disc')}>
              ← Quay lại
            </Button>
            <Button
              className="flex-1"
              disabled={personalityDone < totalPersonalityQs || submitting}
              onClick={submit}
            >
              {submitting
                ? 'Đang nộp bài…'
                : personalityDone < totalPersonalityQs
                  ? `Trả lời đủ để nộp (còn ${totalPersonalityQs - personalityDone})`
                  : 'Nộp bài'}
            </Button>
          </div>
        </section>
      )}
    </div>
  );
}
