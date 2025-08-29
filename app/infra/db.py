import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
load_dotenv() 

"""
DATABASE_URL → reads the env variable , map to Postgres
create_async_engine(...) → creates the engine, which is the gateway between SQLAlchemy and Postgres DB.
AsyncSessionLocal → a “factory” that creates sessions (conversations with the DB).
Base = declarative_base() → a parent class that all models (tables) inherit from.
get_session() → a FastAPI dependency to automatically give a session inside request handlers.
"""


DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Example: "
                       "sqlite+aiosqlite:///./dev.db or "
                       "postgresql+asyncpg://user:pass@host:5432/dbname")


engine = create_async_engine(DATABASE_URL, future=True, echo=True)  # echo=True prints SQL
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_session():
    async with AsyncSessionLocal() as session:
        yield session