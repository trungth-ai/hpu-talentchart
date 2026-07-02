-- Init database — chạy 1 lần khi container PostgreSQL khởi tạo volume mới
-- Schema thật do Alembic migration quản lý (uv run alembic upgrade head)

-- UTF-8 đã là mặc định của image postgres:16-alpine (db-conventions.md)
-- pgcrypto: phòng khi cần gen_random_uuid() ở tầng SQL
CREATE EXTENSION IF NOT EXISTS pgcrypto;
