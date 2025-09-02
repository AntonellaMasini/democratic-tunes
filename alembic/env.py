from logging.config import fileConfig
import os, sys

from alembic import context

sys.path.append(os.path.abspath("."))

# Load environment variables from .env 
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Alembic Config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- Import Base so Alembic can autogenerate ----
from app.infra.db import Base  # 
import app.domain.models 
target_metadata = Base.metadata

# ---- Use async engine ---
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

def get_url() -> str:
    
    url = os.getenv("DATABASE_URL")
    if not url:
        # Optional: fall back to alembic.ini's sqlalchemy.url
        url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("DATABASE_URL is not set and sqlalchemy.url is empty.")
    return url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # detect column type changes
        compare_server_default=True
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' (async) mode."""
    # Inject URL dynamically instead of relying on alembic.ini
    config_section = config.get_section(config.config_ini_section) or {}
    config_section["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        config_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    import asyncio
    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
