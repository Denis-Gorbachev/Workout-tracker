from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import psycopg2
from Schemas import *

engine = create_async_engine(
    url="postgresql+asyncpg://postgres:12345@localhost:5432/postgres", echo=True
)

async def init_models():
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
    )

async def get_session():
    async with async_session() as session:
        yield session