# API Reference — TalentChart

> Base URL: `/api/v1` · Envelope chuẩn `{status, data, message[, meta]}` (xem `~/hpu-dev/_shared/api-conventions.md`)
> Auth: `Authorization: Bearer {access_token}` · Tenant resolve: JWT → subdomain → `X-Org-Slug` (chỉ dev)
> Cross-tenant access LUÔN trả 404. Cập nhật: 2026-07-03.

## Auth

| Method | Endpoint | Auth | Ghi chú |
|---|---|---|---|
| POST | `/auth/login` | — | Cần tenant context (subdomain hoặc X-Org-Slug). Rate-limit 5/phút/IP. Trả access (15p) + refresh (7 ngày) + user |
| POST | `/auth/refresh` | — | Body `{refresh_token}` → cặp token mới |
| GET | `/auth/me` | ✅ | Thông tin user hiện tại |

JWT access claims: `sub` (user_id), `organization_id`, `org_role`, `system_role`, `type=access`.

### Google OAuth (ADR-004)

| Method | Endpoint | Auth | Ghi chú |
|---|---|---|---|
| POST | `/auth/google` | — | STAFF: body `{id_token}` (từ Google Identity Services). Email phải thuộc `org.settings.google_workspace_domain` (HPU = hpu.edu.vn) → 403 nếu sai domain. User mới auto-provision role `member`. Rate-limit 5/phút |
| POST | `/public/auth/google` | — | ỨNG VIÊN: Google bất kỳ (email verified), find-or-create candidate theo email trong tenant (subdomain). Trả `candidate_token` (JWT `type=candidate`, 60 phút) — không vào được API quản trị |

## Candidate Portal (token type=candidate)

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/public/candidates/me` | Trạng thái hồ sơ của chính ứng viên |
| GET | `/public/candidates/me/test` | Link bài test đang mở (404 nếu chưa được gửi) |

## Test DISC (port từ SmartHire — có test parity)

| Method | Endpoint | Auth | Ghi chú |
|---|---|---|---|
| POST | `/test-links` | ≥ hr_manager | Body `{candidate_id, expires_hours=72}`. Candidate phải ở SCREENING (tự chuyển TEST_SENT) hoặc TEST_SENT (gửi lại — link cũ bị vô hiệu) |
| GET | `/test-links` | ≥ hr_manager | Danh sách link, filter `candidate_id` |
| GET | `/test-links/candidates/{id}/result` | ≥ hr_manager | Kết quả ĐẦY ĐỦ: DISC + 9 nhóm tính cách + phân tích + gợi ý câu hỏi phỏng vấn. ⚠️ Chỉ là tín hiệu tham khảo, không phải yếu tố quyết định duy nhất |
| GET | `/public/test/{token}` | — | Câu hỏi (40 DISC + 30 personality) — KHÔNG kèm đáp án mapping |
| POST | `/public/test/{token}/submit` | — | Body `{disc_answers, personality_answers}`. Chấm điểm server-side, candidate TEST_SENT→TEST_DONE. Ứng viên chỉ nhận Behavioural Layer. Rate-limit 10/phút |

## Users (role ≥ hr_manager)

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/users` | Pagination `page/per_page`, `search`, `include_inactive` |
| GET | `/users/{id}` | 404 nếu khác tenant |

## Campaigns (role ≥ hr_manager)

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/campaigns` | Filter `status`, `search`; mặc định ẩn inactive |
| GET | `/campaigns/{id}` | |
| POST | `/campaigns` | Tạo với status `draft`. Lương Integer VNĐ, validate min ≤ max, start ≤ end |
| PUT | `/campaigns/{id}` | Partial update, đổi được `status` (draft/open/closed) |
| DELETE | `/campaigns/{id}` | Soft delete (`status=inactive`) |

## Candidates (role ≥ hr_manager)

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/candidates` | Filter `pipeline_stage`, `candidate_type`, `campaign_id`, `search` |
| GET | `/candidates/stats` | Đếm theo 8 pipeline stage (dashboard) |
| GET | `/candidates/{id}` | |
| POST | `/candidates` | `pipeline_stage` client gửi bị bỏ qua — luôn bắt đầu `NEW`. `campaign_id` khác tenant → 404 |
| PUT | `/candidates/{id}` | Partial update. `epa_consent=false` → tự xóa dữ liệu sinh |
| POST | `/candidates/{id}/transition` | Body `{target_stage}`. CHỈ tuần tự `NEW→SCREENING→TEST_SENT→TEST_DONE→INTERVIEW→DECISION→HIRED/REJECTED`, vi phạm → 422 `BUSINESS_RULE_ERROR` |
| DELETE | `/candidates/{id}/epa-data` | Xóa dữ liệu sinh trắc (NĐ 13/2023 — quyền xóa) |
| DELETE | `/candidates/{id}` | Soft delete |

Dữ liệu EPA (`birth_date`, `birth_time`, `birth_place`) chỉ nhận khi `epa_consent=true`; không bao giờ trả về trong response.

## Job Posts (role ≥ hr_manager)

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/job-posts` | Filter `is_published`, `search` |
| GET | `/job-posts/{id}` | |
| POST | `/job-posts` | Slug tự sinh từ title (bỏ dấu tiếng Việt), unique trong org → 409 nếu trùng |
| PUT | `/job-posts/{id}` | Partial update |
| POST | `/job-posts/{id}/publish` | Đăng lên career page |
| POST | `/job-posts/{id}/unpublish` | Gỡ khỏi career page |
| DELETE | `/job-posts/{id}` | Soft delete + tự unpublish |

## Public Career Page (không cần auth, resolve theo subdomain)

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/public/jobs` | Chỉ tin đã publish của tenant theo subdomain; không có tenant → 404 |
| GET | `/public/jobs/{slug}` | Chi tiết tin (không lộ campaign_id/status nội bộ) |
| POST | `/public/jobs/{slug}/apply` | Tạo candidate `NEW`, source `career_page`. Rate-limit 10/phút/IP. Nộp trùng → 422 |

## EPA — Eastern Personality Assessment (port từ Fortune HR, có test parity 300 case)

⚠️ Toàn bộ nhóm này yêu cầu: (1) `org.settings.eastern_layer_enabled = true` (mặc định TẮT — Critical Business Rules), (2) candidate đã `epa_consent` + có `birth_date` (NĐ 13/2023). Mọi response kèm `disclaimer` — kết quả chỉ là tín hiệu tham khảo.

| Method | Endpoint | Auth | Ghi chú |
|---|---|---|---|
| GET | `/epa/today` | ≥ hr_manager | Can Chi hôm nay (dashboard) |
| GET | `/epa/candidates/{id}/zodiac` | ≥ hr_manager | Can Chi/Nạp Âm/Mệnh (tính theo NĂM ÂM LỊCH — 1/1/1938 → Đinh Sửu) |
| GET | `/epa/compatibility?candidate1_id&candidate2_id` | ≥ hr_manager | Điểm tương hợp: 50 +25 tam hợp −30 xung, kẹp 0-100 |
| POST | `/epa/team-suggest` | ≥ hr_manager | Body `{size, department?, candidate_type=employee}` — 3 phương án xếp hạng theo điểm tam hợp |

## Import nhân sự (script — không phải API)

```bash
# Từ backend/ — import file Excel lương (candidate_type=employee, pipeline HIRED)
python scripts/import_employees.py --file "Luong T8.xlsx" --org-slug hpu [--with-epa-consent] [--dry-run]
```
Ngày sinh CHỈ import khi `--with-epa-consent`. Không import cột lương. Email đặt placeholder `@import.hpu.edu.vn` — cập nhật email thật để match Google login.

## System

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/health` | Healthcheck (ngoài `/api/v1`) |

## Error codes

Xem `.claude/rules/api-response.md`: `NOT_FOUND` 404, `VALIDATION_ERROR` 422, `BUSINESS_RULE_ERROR` 422, `DUPLICATE` 409, `FORBIDDEN` 403 (chỉ system permission), `UNAUTHORIZED` 401, `RATE_LIMIT` 429, `INTERNAL_ERROR` 500.
