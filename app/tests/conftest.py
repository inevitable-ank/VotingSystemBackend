import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Generator
import uuid
from datetime import datetime, timedelta

from app.main import app
from app.core.db import Base, get_db
from app.models.poll import Poll
from app.models.user import User
from app.models.vote import Vote
from app.models.like import Like
from app.models.option import Option
from app.core.security import get_password_hash

# Test database URL (in-memory SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for testing."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create database session for testing."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_poll(db_session, test_user):
    """Create a test poll."""
    poll = Poll(
        id=uuid.uuid4(),
        title="Test Poll",
        description="This is a test poll",
        slug="test-poll",
        author_id=test_user.id,
        is_active=True,
        allow_multiple=False,
        is_public=True,
        expires_at=datetime.now() + timedelta(days=7)
    )
    db_session.add(poll)
    db_session.commit()
    db_session.refresh(poll)
    
    # Create options
    option1 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Option 1",
        position=0,
        vote_count=0
    )
    option2 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Option 2",
        position=1,
        vote_count=0
    )
    
    db_session.add(option1)
    db_session.add(option2)
    db_session.commit()
    
    return poll


@pytest.fixture
def test_vote(db_session, test_poll, test_user):
    """Create a test vote."""
    # Get first option
    option = db_session.query(Option).filter(Option.poll_id == test_poll.id).first()
    
    vote = Vote(
        id=uuid.uuid4(),
        poll_id=test_poll.id,
        option_id=option.id,
        user_id=test_user.id,
        ip_address="127.0.0.1"
    )
    db_session.add(vote)
    db_session.commit()
    db_session.refresh(vote)
    return vote


@pytest.fixture
def test_like(db_session, test_poll, test_user):
    """Create a test like."""
    like = Like(
        id=uuid.uuid4(),
        poll_id=test_poll.id,
        user_id=test_user.id,
        ip_address="127.0.0.1"
    )
    db_session.add(like)
    db_session.commit()
    db_session.refresh(like)
    return like


@pytest.fixture
def anonymous_user_id():
    """Generate anonymous user ID for testing."""
    return f"anon_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def expired_poll(db_session, test_user):
    """Create an expired test poll."""
    poll = Poll(
        id=uuid.uuid4(),
        title="Expired Poll",
        description="This poll has expired",
        slug="expired-poll",
        author_id=test_user.id,
        is_active=True,
        allow_multiple=False,
        is_public=True,
        expires_at=datetime.now() - timedelta(days=1)  # Expired yesterday
    )
    db_session.add(poll)
    db_session.commit()
    db_session.refresh(poll)
    
    # Create options
    option1 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Expired Option 1",
        position=0,
        vote_count=0
    )
    option2 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Expired Option 2",
        position=1,
        vote_count=0
    )
    
    db_session.add(option1)
    db_session.add(option2)
    db_session.commit()
    
    return poll


@pytest.fixture
def multiple_choice_poll(db_session, test_user):
    """Create a multiple choice test poll."""
    poll = Poll(
        id=uuid.uuid4(),
        title="Multiple Choice Poll",
        description="This poll allows multiple votes",
        slug="multiple-choice-poll",
        author_id=test_user.id,
        is_active=True,
        allow_multiple=True,
        is_public=True,
        expires_at=datetime.now() + timedelta(days=7)
    )
    db_session.add(poll)
    db_session.commit()
    db_session.refresh(poll)
    
    # Create options
    option1 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Multiple Option 1",
        position=0,
        vote_count=0
    )
    option2 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Multiple Option 2",
        position=1,
        vote_count=0
    )
    option3 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Multiple Option 3",
        position=2,
        vote_count=0
    )
    
    db_session.add(option1)
    db_session.add(option2)
    db_session.add(option3)
    db_session.commit()
    
    return poll


@pytest.fixture
def private_poll(db_session, test_user):
    """Create a private test poll."""
    poll = Poll(
        id=uuid.uuid4(),
        title="Private Poll",
        description="This is a private poll",
        slug="private-poll",
        author_id=test_user.id,
        is_active=True,
        allow_multiple=False,
        is_public=False,
        expires_at=datetime.now() + timedelta(days=7)
    )
    db_session.add(poll)
    db_session.commit()
    db_session.refresh(poll)
    
    # Create options
    option1 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Private Option 1",
        position=0,
        vote_count=0
    )
    option2 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Private Option 2",
        position=1,
        vote_count=0
    )
    
    db_session.add(option1)
    db_session.add(option2)
    db_session.commit()
    
    return poll


@pytest.fixture
def inactive_poll(db_session, test_user):
    """Create an inactive test poll."""
    poll = Poll(
        id=uuid.uuid4(),
        title="Inactive Poll",
        description="This poll is inactive",
        slug="inactive-poll",
        author_id=test_user.id,
        is_active=False,
        allow_multiple=False,
        is_public=True,
        expires_at=datetime.now() + timedelta(days=7)
    )
    db_session.add(poll)
    db_session.commit()
    db_session.refresh(poll)
    
    # Create options
    option1 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Inactive Option 1",
        position=0,
        vote_count=0
    )
    option2 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Inactive Option 2",
        position=1,
        vote_count=0
    )
    
    db_session.add(option1)
    db_session.add(option2)
    db_session.commit()
    
    return poll


# Helper functions for tests
def create_test_user(db_session, username="testuser", email="test@example.com"):
    """Helper function to create a test user."""
    user = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_test_poll(db_session, user_id, title="Test Poll", allow_multiple=False, is_public=True):
    """Helper function to create a test poll."""
    poll = Poll(
        id=uuid.uuid4(),
        title=title,
        description=f"Description for {title}",
        slug=title.lower().replace(" ", "-"),
        author_id=user_id,
        is_active=True,
        allow_multiple=allow_multiple,
        is_public=is_public,
        expires_at=datetime.now() + timedelta(days=7)
    )
    db_session.add(poll)
    db_session.commit()
    db_session.refresh(poll)
    
    # Create default options
    option1 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Option 1",
        position=0,
        vote_count=0
    )
    option2 = Option(
        id=uuid.uuid4(),
        poll_id=poll.id,
        text="Option 2",
        position=1,
        vote_count=0
    )
    
    db_session.add(option1)
    db_session.add(option2)
    db_session.commit()
    
    return poll


def create_test_vote(db_session, poll_id, option_id, user_id=None, anon_id=None):
    """Helper function to create a test vote."""
    vote = Vote(
        id=uuid.uuid4(),
        poll_id=poll_id,
        option_id=option_id,
        user_id=user_id,
        anon_id=anon_id,
        ip_address="127.0.0.1"
    )
    db_session.add(vote)
    db_session.commit()
    db_session.refresh(vote)
    return vote


def create_test_like(db_session, poll_id, user_id=None, anon_id=None):
    """Helper function to create a test like."""
    like = Like(
        id=uuid.uuid4(),
        poll_id=poll_id,
        user_id=user_id,
        anon_id=anon_id,
        ip_address="127.0.0.1"
    )
    db_session.add(like)
    db_session.commit()
    db_session.refresh(like)
    return like

