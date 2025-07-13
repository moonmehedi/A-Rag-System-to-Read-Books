from .user import User  # Import User model first
from .chat_message import ChatMessage  # Then import ChatMessage that depends on User


# This ensures models are registered with SQLAlchemy in the correct order
# User must be registered before ChatMessage since ChatMessage has a foreign key to User