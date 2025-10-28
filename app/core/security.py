from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import secrets
import hashlib
import uuid
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: The plain text password
        
    Returns:
        str: The hashed password
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Token creation error: {e}")
        raise


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Optional[dict]: The decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return None


def generate_anonymous_id() -> str:
    """
    Generate a unique anonymous ID for users who don't log in.
    
    Returns:
        str: A unique anonymous identifier
    """
    return str(uuid.uuid4())


def generate_session_token() -> str:
    """
    Generate a secure session token.
    
    Returns:
        str: A secure random token
    """
    return secrets.token_urlsafe(32)


def hash_anonymous_id(anon_id: str) -> str:
    """
    Hash an anonymous ID for storage (one-way hash).
    
    Args:
        anon_id: The anonymous ID to hash
        
    Returns:
        str: The hashed anonymous ID
    """
    return hashlib.sha256(anon_id.encode()).hexdigest()


def create_csrf_token() -> str:
    """
    Create a CSRF token.
    
    Returns:
        str: A CSRF token
    """
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, session_token: str) -> bool:
    """
    Verify a CSRF token.
    
    Args:
        token: The CSRF token to verify
        session_token: The session token
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    # In a real implementation, you'd store and verify against session
    # For now, we'll just check if it's a valid token format
    return len(token) >= 32 and token.isalnum()


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent XSS and other attacks.
    
    Args:
        text: The text to sanitize
        max_length: Maximum length allowed
        
    Returns:
        str: The sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
    sanitized = text
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_poll_title(title: str) -> bool:
    """
    Validate poll title.
    
    Args:
        title: The poll title to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not title or not title.strip():
        return False
    
    sanitized = sanitize_input(title, 200)
    return len(sanitized) >= 3 and len(sanitized) <= 200


def validate_poll_description(description: str) -> bool:
    """
    Validate poll description.
    
    Args:
        description: The poll description to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not description:
        return True  # Description is optional
    
    sanitized = sanitize_input(description, 1000)
    return len(sanitized) <= 1000


def validate_option_text(option_text: str) -> bool:
    """
    Validate poll option text.
    
    Args:
        option_text: The option text to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not option_text or not option_text.strip():
        return False
    
    sanitized = sanitize_input(option_text, 100)
    return len(sanitized) >= 1 and len(sanitized) <= 100


def rate_limit_key(identifier: str, action: str) -> str:
    """
    Generate a rate limiting key.
    
    Args:
        identifier: User or IP identifier
        action: The action being rate limited
        
    Returns:
        str: The rate limiting key
    """
    return f"rate_limit:{action}:{identifier}"


def is_rate_limited(identifier: str, action: str, limit: int, window: int) -> bool:
    """
    Check if an action is rate limited.
    
    Args:
        identifier: User or IP identifier
        action: The action to check
        limit: Maximum number of actions allowed
        window: Time window in seconds
        
    Returns:
        bool: True if rate limited, False otherwise
    """
    # This would typically check against Redis or similar
    # For now, we'll return False (not rate limited)
    return False


def generate_poll_slug(title: str) -> str:
    """
    Generate a URL-friendly slug from poll title.
    
    Args:
        title: The poll title
        
    Returns:
        str: A URL-friendly slug
    """
    import re
    
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = slug.strip('-')
    
    # Add random suffix to ensure uniqueness
    random_suffix = secrets.token_hex(4)
    return f"{slug}-{random_suffix}"


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: The email to validate
        
    Returns:
        bool: True if valid email format, False otherwise
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) if email else False


def validate_username(username: str) -> bool:
    """
    Validate username format.
    
    Args:
        username: The username to validate
        
    Returns:
        bool: True if valid username format, False otherwise
    """
    if not username:
        return False
    
    # Username should be 3-30 characters, alphanumeric and underscores only
    import re
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return bool(re.match(pattern, username))

