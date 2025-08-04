"""remove_ltree_simplify_chat_messages

Revision ID: 28a194bfd8e4
Revises: 632fd2d15da3
Create Date: 2025-07-15 22:37:15.814935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28a194bfd8e4'
down_revision: Union[str, None] = '632fd2d15da3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing chat_messages table
    op.drop_table('chat_messages')
    
    # Recreate chat_messages table without ltree
    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_user', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('doc_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the simplified chat_messages table
    op.drop_table('chat_messages')
    
    # Recreate the old chat_messages table with ltree
    op.execute('CREATE EXTENSION IF NOT EXISTS ltree')
    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('parent_id', sa.UUID(), nullable=True),
        sa.Column('ltree_path', sa.VARCHAR(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_user', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('doc_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
