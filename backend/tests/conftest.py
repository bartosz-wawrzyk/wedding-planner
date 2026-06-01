import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import NullPool

from main import app
from app.db.session import get_db
from app.db.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/Test_wp_4_tests"

engine = create_async_engine(
    TEST_DATABASE_URL, 
    poolclass=NullPool,
    echo=False
)

TestingSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """It creates an event loop for the entire test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS wp"))
        await conn.execute(text("SET search_path TO wp"))
        
        for table in Base.metadata.tables.values():
            table.schema = "wp"
            
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session():
    """It creates a clean session for each test."""
    async with engine.connect() as connection:
        await connection.execute(text("SET search_path TO wp"))
        async with TestingSessionLocal(bind=connection) as session:
            yield session
            
            try:
                await session.rollback()
            except Exception:
                pass
        
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(text(f"TRUNCATE TABLE wp.{table.name} CASCADE"))
            await session.commit()

@pytest_asyncio.fixture
async def client(db_session):
    """
    It injects a test session into FastAPI and creates an asynchronous client.
    We use ASGITransport to ensure compatibility with the latest versions of httpx.
    """
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()