from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url, future=True, echo=settings.debug
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
