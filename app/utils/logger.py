import logging
import sys
from typing import Optional
import structlog
from app.core.config import settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Setup application logging configuration.
    
    Args:
        log_level: Optional log level override
    """
    # Determine log level
    level = log_level or ("DEBUG" if settings.debug else "INFO")
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.environment == "production" 
            else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )
    logging.getLogger("redis").setLevel(logging.WARNING)
    
    # Create application logger
    logger = structlog.get_logger("quickpoll")
    logger.info("Logging configured", level=level, environment=settings.environment)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        structlog.BoundLogger: Structured logger instance
    """
    return structlog.get_logger(name)


class RequestLogger:
    """Logger for HTTP requests."""
    
    def __init__(self):
        self.logger = get_logger("request")
    
    def log_request(self, method: str, path: str, status_code: int, 
                   process_time: float, user_id: Optional[str] = None):
        """
        Log HTTP request details.
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            process_time: Request processing time
            user_id: Optional user ID
        """
        self.logger.info(
            "HTTP request",
            method=method,
            path=path,
            status_code=status_code,
            process_time=process_time,
            user_id=user_id
        )
    
    def log_error(self, method: str, path: str, error: str, 
                 user_id: Optional[str] = None):
        """
        Log HTTP request errors.
        
        Args:
            method: HTTP method
            path: Request path
            error: Error message
            user_id: Optional user ID
        """
        self.logger.error(
            "HTTP request error",
            method=method,
            path=path,
            error=error,
            user_id=user_id
        )


class DatabaseLogger:
    """Logger for database operations."""
    
    def __init__(self):
        self.logger = get_logger("database")
    
    def log_query(self, query: str, params: Optional[dict] = None, 
                 execution_time: Optional[float] = None):
        """
        Log database query.
        
        Args:
            query: SQL query
            params: Query parameters
            execution_time: Query execution time
        """
        self.logger.debug(
            "Database query",
            query=query,
            params=params,
            execution_time=execution_time
        )
    
    def log_error(self, error: str, query: Optional[str] = None):
        """
        Log database error.
        
        Args:
            error: Error message
            query: Optional SQL query
        """
        self.logger.error(
            "Database error",
            error=error,
            query=query
        )


class WebSocketLogger:
    """Logger for WebSocket operations."""
    
    def __init__(self):
        self.logger = get_logger("websocket")
    
    def log_connection(self, client_id: str, poll_id: Optional[str] = None):
        """
        Log WebSocket connection.
        
        Args:
            client_id: Client identifier
            poll_id: Optional poll ID
        """
        self.logger.info(
            "WebSocket connection",
            client_id=client_id,
            poll_id=poll_id
        )
    
    def log_disconnection(self, client_id: str, reason: Optional[str] = None):
        """
        Log WebSocket disconnection.
        
        Args:
            client_id: Client identifier
            reason: Disconnection reason
        """
        self.logger.info(
            "WebSocket disconnection",
            client_id=client_id,
            reason=reason
        )
    
    def log_message(self, client_id: str, message_type: str, poll_id: Optional[str] = None):
        """
        Log WebSocket message.
        
        Args:
            client_id: Client identifier
            message_type: Type of message
            poll_id: Optional poll ID
        """
        self.logger.debug(
            "WebSocket message",
            client_id=client_id,
            message_type=message_type,
            poll_id=poll_id
        )
    
    def log_error(self, client_id: str, error: str):
        """
        Log WebSocket error.
        
        Args:
            client_id: Client identifier
            error: Error message
        """
        self.logger.error(
            "WebSocket error",
            client_id=client_id,
            error=error
        )


class SecurityLogger:
    """Logger for security events."""
    
    def __init__(self):
        self.logger = get_logger("security")
    
    def log_authentication_attempt(self, username: str, success: bool, ip_address: Optional[str] = None):
        """
        Log authentication attempt.
        
        Args:
            username: Username attempted
            success: Whether authentication was successful
            ip_address: Optional IP address
        """
        self.logger.info(
            "Authentication attempt",
            username=username,
            success=success,
            ip_address=ip_address
        )
    
    def log_suspicious_activity(self, activity: str, ip_address: Optional[str] = None, 
                               user_id: Optional[str] = None):
        """
        Log suspicious activity.
        
        Args:
            activity: Description of suspicious activity
            ip_address: Optional IP address
            user_id: Optional user ID
        """
        self.logger.warning(
            "Suspicious activity",
            activity=activity,
            ip_address=ip_address,
            user_id=user_id
        )
    
    def log_rate_limit_exceeded(self, identifier: str, action: str, ip_address: Optional[str] = None):
        """
        Log rate limit exceeded.
        
        Args:
            identifier: User or IP identifier
            action: Action that was rate limited
            ip_address: Optional IP address
        """
        self.logger.warning(
            "Rate limit exceeded",
            identifier=identifier,
            action=action,
            ip_address=ip_address
        )

