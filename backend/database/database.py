"""
Database configuration and connection management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from .models import Base

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/seo_platform")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_database():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def close_database():
    """Close database connections"""
    await engine.dispose()
