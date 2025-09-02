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
from app.infra.db_url import load_db_url

def get_url() -> str:
    # use Alembic config as fallback
    return load_db_url(for_async=True, fallback_config=config)


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
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    cfg = dict(config.get_section(config.config_ini_section) or {})
    cfg["sqlalchemy.url"] = get_url()  # inject normalized async URL

    connectable = async_engine_from_config(
        cfg,
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