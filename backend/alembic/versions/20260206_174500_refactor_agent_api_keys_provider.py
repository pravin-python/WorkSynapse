"""Refactor agent_api_keys provider enum to relational provider_id

Revision ID: a59e839f3cc4
Revises: 2eea265c8b6f
Create Date: 2026-02-06 17:45:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a59e839f3cc4'
down_revision = '2eea265c8b6f'
branch_labels = None
depends_on = None


def upgrade():
    # add provider_id nullable column
    op.add_column('agent_api_keys', sa.Column('provider_id', sa.Integer(), nullable=True))
    op.execute('CREATE INDEX IF NOT EXISTS ix_agent_api_keys_user_provider_id ON agent_api_keys (user_id, provider_id)')

    # populate provider_id from llm_key_providers.type
    op.execute("""
        UPDATE agent_api_keys
        SET provider_id = (
            SELECT id FROM llm_key_providers WHERE llm_key_providers.type::text = agent_api_keys.provider::text LIMIT 1
        )
        WHERE provider IS NOT NULL
    """)

    # make provider_id non-nullable after population
    op.alter_column('agent_api_keys', 'provider_id', nullable=False)

    # add FK constraint
    op.create_foreign_key('agent_api_keys_provider_id_fkey', 'agent_api_keys', 'llm_key_providers', ['provider_id'], ['id'], ondelete='RESTRICT')

    # drop old enum column and index
    op.drop_index('ix_agent_api_keys_user_provider', table_name='agent_api_keys')
    op.drop_column('agent_api_keys', 'provider')

    # drop enum type if present
    try:
        op.execute('DROP TYPE IF EXISTS agentmodelprovider')
    except Exception:
        pass


def downgrade():
    # recreate enum type (best effort)
    try:
        op.execute("CREATE TYPE agentmodelprovider AS ENUM ('openai','anthropic','google','gemini','ollama','huggingface','azure_openai','custom','groq')")
    except Exception:
        pass

    # add provider enum column back
    op.add_column('agent_api_keys', sa.Column('provider', postgresql.ENUM(name='agentmodelprovider'), nullable=True))

    # populate provider from llm_key_providers
    op.execute("""
        UPDATE agent_api_keys
        SET provider = (
            SELECT llm_key_providers.type::text FROM llm_key_providers WHERE llm_key_providers.id = agent_api_keys.provider_id LIMIT 1
        )
        WHERE provider_id IS NOT NULL
    """)

    # drop FK and provider_id
    op.drop_constraint('agent_api_keys_provider_id_fkey', 'agent_api_keys', type_='foreignkey')
    op.drop_index('ix_agent_api_keys_user_provider_id', table_name='agent_api_keys')
    op.drop_column('agent_api_keys', 'provider_id')

    # recreate old index
    op.create_index('ix_agent_api_keys_user_provider', 'agent_api_keys', ['user_id', 'provider'])