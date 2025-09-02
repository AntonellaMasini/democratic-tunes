import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from app.infra.db_url import load_db_url

load_dotenv() 

"""
DATABASE_URL → reads the env variable , map to Postgres
create_async_engine(...) → creates the engine, which is the gateway between SQLAlchemy and Postgres DB.
AsyncSessionLocal → a “factory” that creates sessions (conversations with the DB).
Base = declarative_base() → a parent class that all models (tables) inherit from.
get_session() → a FastAPI dependency to automatically give a session inside request handlers.
"""

# Build the normalized async URL (works locally and on Fly)
DATABASE_URL = load_db_url(for_async=True)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true", # if SQL_ECHO is set to "true", the engine will log all SQL statements it runs (for debug)
    pool_pre_ping=True, # enables a connection health check (ping), runs a lightweight test query (aka SELECT 1) right before giving the connection to the app
    connect_args={"ssl": False},   # tell asyncpg: no TLS
)

AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session