"""update_llm_provider_enum

Revision ID: db58215d0632
Revises: 4c174dfda502
Create Date: 2026-02-06 12:47:15.316669+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db58215d0632'
down_revision: Union[str, None] = '4c174dfda502'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We must operate outside of a transaction block for ALTER TYPE ADD VALUE
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE llmkeyprovidertype ADD VALUE IF NOT EXISTS 'AZURE_OPENAI'")
        op.execute("ALTER TYPE llmkeyprovidertype ADD VALUE IF NOT EXISTS 'AWS_BEDROCK'")
        op.execute("ALTER TYPE llmkeyprovidertype ADD VALUE IF NOT EXISTS 'DEEPSEEK'")


def downgrade() -> None:
    # Downgrading enum values in Postgres is complex and usually not done for additions
    pass
