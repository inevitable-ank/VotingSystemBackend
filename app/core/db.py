from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database engine configuration
engine_kwargs = {
    "echo": settings.database_echo,
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Handle SQLite for testing
if settings.database_url.startswith("sqlite"):
    engine_kwargs.update({
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False}
    })

# Create database engine
engine = create_engine(
    settings.database_url,
    **engine_kwargs
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get database information.
    
    Returns:
        dict: Database information including URL (masked) and status
    """
    # Mask password in URL for logging
    masked_url = settings.database_url
    if "@" in masked_url:
        parts = masked_url.split("@")
        if len(parts) == 2:
            user_pass = parts[0].split("//")[-1]
            if ":" in user_pass:
                user, _ = user_pass.split(":", 1)
                masked_url = masked_url.replace(user_pass, f"{user}:***")
    
    return {
        "url": masked_url,
        "echo": settings.database_echo,
        "connected": check_database_connection(),
        "pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A",
        "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else "N/A"
    }


# Database health check
def health_check() -> dict:
    """
    Perform database health check.
    
    Returns:
        dict: Health check results
    """
    try:
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT 1 as health_check"))
            health_status = result.fetchone()[0] == 1
        
        return {
            "status": "healthy" if health_status else "unhealthy",
            "database": "connected" if health_status else "disconnected",
            "timestamp": "2024-01-01T00:00:00Z"  # You can use datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }
