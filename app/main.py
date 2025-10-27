from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from app.core.config import settings
from app.core.db import create_tables, check_database_connection, health_check
from app.core.redis_client import get_redis_client
from app.utils.exceptions import CustomException
from app.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting QuickPoll application...")
    
    try:
        # Check database connection
        if not check_database_connection():
            logger.error("Failed to connect to database")
            raise Exception("Database connection failed")
        
        # Create database tables
        create_tables()
        logger.info("Database tables created/verified")
        
        # Test Redis connection
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.ping()
            logger.info("Redis connection successful")
        else:
            logger.warning("Redis connection failed - continuing without Redis")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down QuickPoll application...")
    # Add any cleanup logic here if needed


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A real-time polling platform built with FastAPI and Next.js",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["your-domain.com", "*.your-domain.com"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    """Handle custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal server error occurred",
            "details": str(exc) if settings.debug else None
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check_endpoint():
    """
    Health check endpoint for monitoring.
    """
    try:
        db_health = health_check()
        redis_health = {"status": "unknown"}
        
        # Check Redis if available
        redis_client = await get_redis_client()
        if redis_client:
            try:
                await redis_client.ping()
                redis_health = {"status": "healthy"}
            except Exception as e:
                redis_health = {"status": "unhealthy", "error": str(e)}
        
        overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "version": settings.app_version,
            "environment": settings.environment,
            "services": {
                "database": db_health,
                "redis": redis_health
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else "disabled",
        "health_check": "/health"
    }


# API information endpoint
@app.get("/api/info", tags=["API"])
async def api_info():
    """
    Get API information and configuration.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "features": {
            "websockets": True,
            "rate_limiting": True,
            "caching": True,
            "authentication": True
        },
        "limits": {
            "max_poll_options": 10,
            "max_poll_title_length": 200,
            "max_poll_description_length": 1000,
            "max_option_text_length": 100
        }
    }


# Include API routes
from app.routes import poll_routes, vote_routes, user_routes, like_routes, websocket_routes

app.include_router(poll_routes.router, prefix="/api/polls", tags=["Polls"])
app.include_router(vote_routes.router, prefix="/api/votes", tags=["Votes"])
app.include_router(user_routes.router, prefix="/api/users", tags=["Users"])
app.include_router(like_routes.router, prefix="/api/likes", tags=["Likes"])
app.include_router(websocket_routes.router, prefix="/ws", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning"
    )
