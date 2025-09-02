# alembic/env.py
from logging.config import fileConfig
import os, sys
from alembic import context

sys.path.append(os.path.abspath("."))

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from app.infra.db_url import load_db_url  # <- keep using your normalizer

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.infra.db import Base
import app.domain.models
target_metadata = Base.metadata

from sqlalchemy import pool, engine_from_config

def get_url() -> str:
    # IMPORTANT: sync URL for Alembic (psycopg)
    return load_db_url(for_async=False, fallback_config=config)

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
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
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = get_url()   # inject normalized sync URL

    connectable = engine_from_config(
        cfg, prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
