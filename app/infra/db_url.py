import os
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

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

    # convert sslmode (psycopg) to ssl (asyncpg) or drop it
    url = _normalize_ssl_query(url, for_async=for_async)


    # 2) Add/remove async driver
    if for_async:
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)

    return url

def _normalize_ssl_query(url: str, *, for_async: bool) -> str:
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query, keep_blank_values=True))
    host = parts.hostname or ""

    # Drop psycopg-style sslmode unconditionally
    mode = (q.pop("sslmode", "") or "").lower()

    # Fly internal DB hosts typically end with .internal or .flycast → no TLS
    is_internal = host.endswith(".internal") or host.endswith(".flycast")

    if for_async:
        # asyncpg uses ?ssl=true to force TLS; otherwise it’s plain.
        if not is_internal and mode in ("require", "verify-ca", "verify-full"):
            q["ssl"] = "true"
        else:
            q.pop("ssl", None)  # ensure no leftover

    new_query = urlencode(q, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))