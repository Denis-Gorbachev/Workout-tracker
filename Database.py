from sqlalchemy import ForeignKey, String, create_engine, text, select, TIMESTAMP, func, Integer, delete, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, declarative_base
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import psycopg2

Base = declarative_base()

class Users(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(40), nullable=False)

engine = create_async_engine(
    url="postgresql+asyncpg://postgres:12345@localhost:5432/postgres"
)

# try:
#    with engine.connect() as con:
#     print("Соединение с базой данных успешно установлено.")
# except Exception as e:
#     print(f"Ошибка при подключении к базе данных: {e}")

async def init_models():
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
    )

async def get_session():
    async with async_session() as session:
        yield session
