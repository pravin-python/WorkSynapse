"""add_groq_to_agent_builder_enum

Revision ID: 3d710f3a3cba
Revises: e83d04b1d7f4
Create Date: 2026-02-06 11:31:33.245012+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d710f3a3cba'
down_revision: Union[str, None] = 'e83d04b1d7f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE agentmodelprovider ADD VALUE 'groq'")


def downgrade() -> None:
    pass
