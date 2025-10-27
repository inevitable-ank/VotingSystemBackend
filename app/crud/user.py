from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password, generate_anonymous_id
from app.utils.exceptions import UserNotFoundError, ConflictError, ValidationError

logger = logging.getLogger(__name__)


class UserCRUD:
    """CRUD operations for User model."""
    
    def create(self, db: Session, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_data: User creation data
            
        Returns:
            User: Created user
            
        Raises:
            ConflictError: If username or email already exists
        """
        # Check if username already exists
        if self.get_by_username(db, user_data.username):
            raise ConflictError(f"Username '{user_data.username}' already exists")
        
        # Check if email already exists
        if user_data.email and self.get_by_email(db, user_data.email):
            raise ConflictError(f"Email '{user_data.email}' already exists")
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower() if user_data.email else None,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User created: {db_user.username}")
        return db_user
    
    def get(self, db: Session, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username.lower()).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email.lower()).first()
    
    def get_multiple(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get multiple users with pagination."""
        return db.query(User).offset(skip).limit(limit).all()
    
    def update(self, db: Session, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Update user.
        
        Args:
            db: Database session
            user_id: User ID
            user_data: Update data
            
        Returns:
            User: Updated user or None if not found
        """
        db_user = self.get(db, user_id)
        if not db_user:
            return None
        
        # Check for conflicts
        if user_data.username and user_data.username != db_user.username:
            existing_user = self.get_by_username(db, user_data.username)
            if existing_user:
                raise ConflictError(f"Username '{user_data.username}' already exists")
        
        if user_data.email and user_data.email != db_user.email:
            existing_user = self.get_by_email(db, user_data.email)
            if existing_user:
                raise ConflictError(f"Email '{user_data.email}' already exists")
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User updated: {db_user.username}")
        return db_user
    
    def delete(self, db: Session, user_id: UUID) -> bool:
        """
        Delete user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        db_user = self.get(db, user_id)
        if not db_user:
            return False
        
        db.delete(db_user)
        db.commit()
        
        logger.info(f"User deleted: {db_user.username}")
        return True
    
    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password.
        
        Args:
            db: Database session
            username: Username or email
            password: Password
            
        Returns:
            User: Authenticated user or None
        """
        # Try username first
        user = self.get_by_username(db, username)
        
        # If not found, try email
        if not user and '@' in username:
            user = self.get_by_email(db, username)
        
        if not user or not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_anonymous(self, db: Session, anon_id: str) -> User:
        """
        Create anonymous user.
        
        Args:
            db: Database session
            anon_id: Anonymous user ID
            
        Returns:
            User: Anonymous user
        """
        username = f"anon_{anon_id[:8]}"
        
        # Ensure unique username
        counter = 1
        original_username = username
        while self.get_by_username(db, username):
            username = f"{original_username}_{counter}"
            counter += 1
        
        db_user = User(
            username=username,
            email=None,
            hashed_password=None,
            is_active=True,
            is_verified=False
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Anonymous user created: {db_user.username}")
        return db_user
    
    def get_stats(self, db: Session, user_id: UUID) -> Dict[str, Any]:
        """Get user statistics."""
        user = self.get(db, user_id)
        if not user:
            raise UserNotFoundError(str(user_id))
        
        return {
            "total_polls": len(user.polls),
            "total_votes": len(user.votes),
            "total_likes": len(user.likes),
            "polls_created_today": db.query(User).filter(
                User.id == user_id,
                func.date(User.created_at) == func.current_date()
            ).count(),
            "votes_cast_today": db.query(User).filter(
                User.id == user_id,
                func.date(User.created_at) == func.current_date()
            ).count(),
            "likes_given_today": db.query(User).filter(
                User.id == user_id,
                func.date(User.created_at) == func.current_date()
            ).count()
        }
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 20) -> List[User]:
        """Search users by username or email."""
        return db.query(User).filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        ).offset(skip).limit(limit).all()
    
    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users."""
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def deactivate(self, db: Session, user_id: UUID) -> bool:
        """Deactivate user."""
        db_user = self.get(db, user_id)
        if not db_user:
            return False
        
        db_user.is_active = False
        db.commit()
        
        logger.info(f"User deactivated: {db_user.username}")
        return True
    
    def activate(self, db: Session, user_id: UUID) -> bool:
        """Activate user."""
        db_user = self.get(db, user_id)
        if not db_user:
            return False
        
        db_user.is_active = True
        db.commit()
        
        logger.info(f"User activated: {db_user.username}")
        return True


# Create instance
user_crud = UserCRUD()
