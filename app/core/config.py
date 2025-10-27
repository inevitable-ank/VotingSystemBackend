from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    app_name: str = "QuickPoll"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database Configuration
    database_url: str = "postgresql://postgres:password@localhost:5432/quickpoll"
    database_echo: bool = False
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    
    # Security Configuration
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Configuration
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-frontend-domain.com"
    ]
    
    # WebSocket Configuration
    websocket_heartbeat_interval: int = 30
    websocket_max_connections: int = 1000
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # File Upload Configuration
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    allowed_file_types: list[str] = ["image/jpeg", "image/png", "image/gif"]
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database URL with fallback to environment variable."""
    return os.getenv("DATABASE_URL", settings.database_url)


def get_redis_url() -> str:
    """Get Redis URL with fallback to environment variable."""
    return os.getenv("REDIS_URL", settings.redis_url)


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return settings.environment.lower() == "development"
