from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_utils import LtreeType, Ltree
from sqlalchemy.orm import relationship, Mapped
import uuid
import datetime
from app.db.session import Base
from typing import Optional

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    @property
    def ltree_path_str(self) -> str:
        """Convert Ltree to string for serialization"""
        return str(self.ltree_path) if self.ltree_path else ""

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Self-referencing parent ID
    parent_id = Column(UUID(as_uuid=True), ForeignKey("chat_messages.id"), nullable=True)

    # ltree path for hierarchical queries
    ltree_path = Column(LtreeType, nullable=False, index=True)

    def _create_ltree_path(self):
        """Create ltree path based on parent's path or message id if no parent"""
        if not self.ltree_path:
            # If ltree_path is already set (from the route), use that
            # This happens when we explicitly set it during message creation
            if self.parent_id is None:
                # Root message - use its own ID as path
                return Ltree(str(self.id).replace('-', '_'))
            else:
                # Get parent from database
                from sqlalchemy.orm import object_session
                session = object_session(self)
                if session:
                    parent = session.query(ChatMessage).filter(ChatMessage.id == self.parent_id).first()
                    if parent and parent.ltree_path:
                        return Ltree(f"{str(parent.ltree_path)}.{str(self.id).replace('-', '_')}")
                # Fallback to using just the ID if something goes wrong
                return Ltree(str(self.id).replace('-', '_'))
        return self.ltree_path

    content = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    doc_id = Column(String, nullable=True)

    # ✅ Correct self-referential relationship
    parent = relationship(
        "ChatMessage",
        remote_side=[id],
        foreign_keys=[parent_id],
        backref="children",
        lazy="joined"
    )

    # ✅ Link to User model
    user = relationship("User", backref="messages")

@event.listens_for(ChatMessage, 'before_insert')
def _set_ltree_path(mapper, connection, target):
    target.ltree_path = target._create_ltree_path()
