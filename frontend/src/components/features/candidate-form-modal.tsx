'use client';

// Modal thêm/sửa nhân sự — dùng chung cho create (POST) và edit (PUT)
// Dữ liệu ngày sinh (EPA) chỉ gửi khi tick "đồng ý dùng dữ liệu EPA" (NĐ 13/2023).
// LƯU Ý: API không trả birth_date/time/place (dữ liệu nhạy cảm) nên khi SỬA, các ô
// ngày sinh để trống = giữ nguyên; chỉ nhập khi muốn ghi đè.

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { api, ApiError } from '@/lib/api-client';
import { TYPE_LABELS, type Candidate } from '@/lib/types';

interface Props {
  mode: 'create' | 'edit';
  initial?: Candidate; // prefill khi edit
  onClose: () => void;
}

export function CandidateFormModal({ mode, initial, onClose }: Props) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    full_name: initial?.full_name ?? '',
    email: initial?.email ?? '',
    candidate_type: initial?.candidate_type ?? (mode === 'create' ? 'employee' : 'applicant'),
    employee_code: initial?.employee_code ?? '',
    department: initial?.department ?? '',
    gender: (initial?.gender ?? '') as string,
    position: initial?.position ?? '',
    phone: initial?.phone ?? '',
    source: initial?.source ?? '',
    notes: initial?.notes ?? '',
    epa_consent: initial?.epa_consent ?? false,
    birth_date: '',
    birth_time: '',
    birth_place: '',
  });

  const set = <K extends keyof typeof form>(key: K, value: (typeof form)[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const save = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = {
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        candidate_type: form.candidate_type,
        employee_code: form.employee_code.trim() || null,
        department: form.department.trim() || null,
        gender: form.gender || null,
        position: form.position.trim() || null,
        phone: form.phone.trim() || null,
        source: form.source.trim() || null,
        notes: form.notes.trim() || null,
        epa_consent: form.epa_consent,
      };
      // Ngày sinh chỉ gửi khi có consent + người dùng thực sự nhập (giữ nguyên nếu để trống)
      if (form.epa_consent) {
        if (form.birth_date) payload.birth_date = form.birth_date;
        if (form.birth_time) payload.birth_time = form.birth_time;
        if (form.birth_place.trim()) payload.birth_place = form.birth_place.trim();
      }
      return mode === 'create'
        ? api.post<Candidate>('/api/v1/candidates', payload)
        : api.put<Candidate>(`/api/v1/candidates/${initial!.id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      if (mode === 'edit' && initial) {
        queryClient.invalidateQueries({ queryKey: ['candidate', initial.id] });
      }
      onClose();
    },
    onError: (e) => setError(e instanceof ApiError ? e.message : 'Có lỗi xảy ra, thử lại'),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.full_name.trim() || !form.email.trim()) {
      setError('Vui lòng nhập họ tên và email');
      return;
    }
    save.mutate();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 py-10"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">
            {mode === 'create' ? 'Thêm nhân sự / ứng viên' : `Sửa: ${initial?.full_name}`}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Đóng"
          >
            ✕
          </button>
        </div>

        {error && (
          <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        )}

        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Họ tên *">
              <Input value={form.full_name} onChange={(e) => set('full_name', e.target.value)} />
            </Field>
            <Field label="Email *">
              <Input
                type="email"
                value={form.email}
                onChange={(e) => set('email', e.target.value)}
              />
            </Field>
            <Field label="Loại">
              <select
                value={form.candidate_type}
                onChange={(e) => set('candidate_type', e.target.value as Candidate['candidate_type'])}
                className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
              >
                {Object.entries(TYPE_LABELS).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Điện thoại">
              <Input value={form.phone} onChange={(e) => set('phone', e.target.value)} />
            </Field>
            <Field label="Giới tính">
              <select
                value={form.gender}
                onChange={(e) => set('gender', e.target.value)}
                className="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 text-sm"
              >
                <option value="">—</option>
                <option value="male">Nam</option>
                <option value="female">Nữ</option>
              </select>
            </Field>
            <Field label="Mã nhân sự">
              <Input
                value={form.employee_code}
                onChange={(e) => set('employee_code', e.target.value)}
              />
            </Field>
            <Field label="Bộ phận">
              <Input
                value={form.department}
                onChange={(e) => set('department', e.target.value)}
              />
            </Field>
            <Field label="Vị trí">
              <Input value={form.position} onChange={(e) => set('position', e.target.value)} />
            </Field>
            <Field label="Nguồn">
              <Input value={form.source} onChange={(e) => set('source', e.target.value)} />
            </Field>
          </div>

          <Field label="Ghi chú">
            <textarea
              value={form.notes}
              onChange={(e) => set('notes', e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-400 focus:outline-none"
            />
          </Field>

          <label className="flex items-center gap-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={form.epa_consent}
              onChange={(e) => set('epa_consent', e.target.checked)}
            />
            Đồng ý dùng dữ liệu ngày sinh cho EPA (opt-in, NĐ 13/2023)
          </label>

          {form.epa_consent && (
            <div className="grid gap-4 rounded-lg bg-gray-50 p-3 sm:grid-cols-3">
              <Field label="Ngày sinh">
                <Input
                  type="date"
                  value={form.birth_date}
                  onChange={(e) => set('birth_date', e.target.value)}
                />
              </Field>
              <Field label="Giờ sinh (HH:MM)">
                <Input
                  placeholder="VD: 08:30"
                  value={form.birth_time}
                  onChange={(e) => set('birth_time', e.target.value)}
                />
              </Field>
              <Field label="Nơi sinh">
                <Input
                  value={form.birth_place}
                  onChange={(e) => set('birth_place', e.target.value)}
                />
              </Field>
              {mode === 'edit' && (
                <p className="text-xs text-gray-400 sm:col-span-3">
                  Để trống = giữ nguyên ngày sinh hiện tại (dữ liệu nhạy cảm không hiển thị lại).
                </p>
              )}
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>
              Hủy
            </Button>
            <Button type="submit" disabled={save.isPending}>
              {save.isPending ? 'Đang lưu…' : mode === 'create' ? 'Tạo mới' : 'Lưu thay đổi'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-sm text-gray-500">{label}</label>
      {children}
    </div>
  );
}
