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

## System

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/health` | Healthcheck (ngoài `/api/v1`) |

## Error codes

Xem `.claude/rules/api-response.md`: `NOT_FOUND` 404, `VALIDATION_ERROR` 422, `BUSINESS_RULE_ERROR` 422, `DUPLICATE` 409, `FORBIDDEN` 403 (chỉ system permission), `UNAUTHORIZED` 401, `RATE_LIMIT` 429, `INTERNAL_ERROR` 500.
