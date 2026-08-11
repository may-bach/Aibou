from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config import settings

# Database engine initialization with resilient SQLite fallback
engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def init_database():
    global engine, AsyncSessionLocal
    from src.models.user import Base
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[DATABASE] Primary database connected.")
    except Exception as err:
        print(f"[DATABASE] Primary DB unavailable ({err}). Switching to local SQLite...")
        fallback_url = "sqlite+aiosqlite:///./aibou.db"
        engine = create_async_engine(fallback_url, echo=False)
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[DATABASE] Local SQLite database (aibou.db) active.")

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session