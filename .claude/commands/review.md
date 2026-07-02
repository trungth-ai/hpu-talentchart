# Review — Kiểm tra chất lượng code theo chuẩn HPU
# File: .claude/commands/review.md
# Sử dụng: /review

Review toàn bộ code trong project theo 7 tiêu chí HPU.

## Tiêu chí đánh giá (cho điểm /10 mỗi tiêu chí)

### 1. API Consistency
- Response format đúng envelope {status, data, message}?
- Error codes đúng chuẩn (400, 401, 403, 404, 422)?
- URL naming đúng (kebab-case, plural)?
- Pagination có ở mọi list endpoint?
Tham khảo: ~/hpu-dev/_shared/api-conventions.md

### 2. Database Quality
- Mọi bảng có id, created_at, updated_at, status?
- Naming đúng snake_case?
- Soft delete (không hard delete)?
- Money dùng Integer (không Float)?
- Foreign keys đúng?
Tham khảo: ~/hpu-dev/_shared/db-conventions.md

### 3. Security
- Password hash bằng bcrypt?
- SQL injection: parameterized queries?
- XSS: Jinja2 |e filter cho user input?
- CSRF protection?
- Secrets trong .env (không hardcode)?
- Session httponly, secure?

### 4. UI Consistency
- Dùng đúng color palette HPU (#1e3a5f)?
- Sidebar layout chuẩn?
- Status badge đúng màu?
- Money format N.NNN.NNN đ?
- Empty state, loading state có?
- Confirm trước xóa?
Tham khảo: ~/hpu-dev/_shared/design-system/README.md

### 5. Code Quality
- Type hints cho Python functions?
- Docstrings cho functions quan trọng?
- Error handling (try/except, HTTPException)?
- Không có code duplicate?
- Functions ngắn gọn (<50 dòng)?

### 6. Docker Ready
- Dockerfile multi-stage, non-root user?
- Health endpoint /health?
- Volumes cho data, logs?
- .env.example tồn tại?

### 7. Documentation
- CLAUDE.md cập nhật?
- docs/PLAN.md phản ánh đúng trạng thái?
- docs/API.md liệt kê endpoints?
- README.md có hướng dẫn setup?

## Output Format
```
📊 HPU Code Review — {project_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. API Consistency:    {score}/10  {emoji}
2. Database Quality:   {score}/10  {emoji}
3. Security:           {score}/10  {emoji}
4. UI Consistency:     {score}/10  {emoji}
5. Code Quality:       {score}/10  {emoji}
6. Docker Ready:       {score}/10  {emoji}
7. Documentation:      {score}/10  {emoji}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tổng: {total}/70 — {grade}

🔴 Critical Issues (phải fix ngay):
1. ...

🟡 Improvements (nên fix):
1. ...

🟢 Good Practices (đã tốt):
1. ...
```
