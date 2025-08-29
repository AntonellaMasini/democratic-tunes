"""update nullables in room model

Revision ID: 7a58d137eaa5
Revises: 9c89adf84919
Create Date: 2025-08-29 15:01:53.616870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a58d137eaa5'
down_revision: Union[str, Sequence[str], None] = '9c89adf84919'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():

    op.alter_column("rooms", "host_user_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.alter_column("rooms", "is_active",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("true"),
    )

def downgrade():
    op.alter_column("rooms", "is_active",
        existing_type=sa.Boolean(),
        nullable=True,
        server_default=None,
    )
    op.alter_column("rooms", "host_user_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
    )