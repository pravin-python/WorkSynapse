"""add_groq_to_provider_enum

Revision ID: e83d04b1d7f4
Revises: a2cef8214637
Create Date: 2026-02-06 11:18:47.586225+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e83d04b1d7f4'
down_revision: Union[str, None] = 'a2cef8214637'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE llmkeyprovidertype ADD VALUE 'GROQ'")


def downgrade() -> None:
    pass
