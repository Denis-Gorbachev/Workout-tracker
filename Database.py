from sqlalchemy import String, text, Integer, Float, ForeignKey
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, declarative_base, relationship
# from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import psycopg2
import asyncio

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)
    pwd_hash: Mapped[str] = mapped_column(String(256), nullable=False)

class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=True, unique=True)

class Workout(Base):
    __tablename__ = "workouts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercises.id"))
    sets: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    weights: Mapped[float] = mapped_column(Float, default=0)
    user = relationship("User")
    exercise = relationship("Exercise")

engine = create_async_engine(
    url="postgresql+asyncpg://postgres:12345@localhost:5432/postgres", echo=True
)

async def check_db_exists():
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except OperationalError:
        return False

async def init_models():
    async with engine.connect() as conn:
        db_exists = await check_db_exists()
        # if db_exists:
        #     await conn.execute(text("DROP TABLE users"))
        await conn.run_sync(Base.metadata.create_all)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
    )

async def get_session():
    async with async_session() as session:
        yield session