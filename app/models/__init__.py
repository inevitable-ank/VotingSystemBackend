# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .poll import Poll
from .option import Option
from .vote import Vote
from .like import Like

# Make models available for import
__all__ = ["User", "Poll", "Option", "Vote", "Like"]
