# Alembic env — dùng sync engine (DATABASE_URL_SYNC, psycopg2) cho migration

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Cho phép import app/ khi chạy từ thư mục backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import Base  # noqa: E402 — import sau khi chỉnh sys.path

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# URL lấy từ env — KHÔNG hardcode credential trong alembic.ini
database_url = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://talentchart:talentchart@localhost:5432/talentchart",
)
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Chạy migration ở chế độ offline (sinh SQL, không cần kết nối DB)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migration trực tiếp trên DB."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
