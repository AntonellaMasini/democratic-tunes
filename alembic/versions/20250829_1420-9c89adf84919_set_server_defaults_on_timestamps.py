"""set server defaults on timestamps

Revision ID: 9c89adf84919
Revises: cfe0fccab475
Create Date: 2025-08-29 14:20:07.384468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c89adf84919'
down_revision: Union[str, Sequence[str], None] = 'cfe0fccab475'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False
    )
    op.alter_column("rooms", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False
    )
    op.alter_column("room_members", "joined_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False
    )
    op.alter_column("room_tracks", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False
    )
    op.alter_column("votes", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False
    )


def downgrade() -> None:
    op.alter_column("votes", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
    op.alter_column("room_tracks", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
    op.alter_column("room_members", "joined_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
    op.alter_column("rooms", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
    op.alter_column("users", "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False
    )
