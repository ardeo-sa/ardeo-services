from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import SERVICES_DB_URI

engine = create_async_engine(SERVICES_DB_URI, echo=True)

async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_services_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
