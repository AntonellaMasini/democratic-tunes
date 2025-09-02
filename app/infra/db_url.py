import os

import os
try:
    from dotenv import load_dotenv
    load_dotenv()  # so local "python -c ..."" sees .env
except Exception:
    pass

def load_db_url(*, for_async: bool = True, fallback_config=None) -> str:
    """
    Read DATABASE_URL from env (or an Alembic fallback), normalize scheme/driver.

    - Accepts postgres:// and converts to postgresql://
    - Adds +asyncpg for async engines when needed
    """
    url = os.getenv("DATABASE_URL")
    if not url and fallback_config is not None:
        # e.g., Alembic's Config: config.get_main_option("sqlalchemy.url")
        url = fallback_config.get_main_option("sqlalchemy.url")

    if not url:
        raise RuntimeError("DATABASE_URL is not set and sqlalchemy.url is empty.")

    # 1) Normalize legacy scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # 2) Add/remove async driver
    if for_async:
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

    return url
