"""Agent integration for local models

Revision ID: local_models_002
Revises: local_models_001
Create Date: 2026-02-06 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'local_models_002'
down_revision = 'local_models_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make model_id nullable in custom_agents
    op.alter_column('custom_agents', 'model_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    
    # Add local_model_id to custom_agents
    op.add_column('custom_agents', sa.Column('local_model_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_custom_agents_local_model_id', 'custom_agents', 'local_models', ['local_model_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_custom_agents_local_model_id', 'custom_agents', type_='foreignkey')
    op.drop_column('custom_agents', 'local_model_id')
    
    # Make model_id not nullable again (warning: this might fail if there are nulls)
    # op.alter_column('custom_agents', 'model_id',
    #            existing_type=sa.INTEGER(),
    #            nullable=False)
