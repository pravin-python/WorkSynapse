"""Refactor agent_api_keys provider enum to relational provider_id

Revision ID: 20260206_174500_refactor_agent_api_keys_provider
Revises: 20260206_133223_refactor_llm_models_structure
Create Date: 2026-02-06 17:45:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260206_174500_refactor_agent_api_keys_provider'
"""Refactor agent_api_keys provider enum to relational provider_id

Revision ID: 20260206_174500_refactor_agent_api_keys_provider
Revises: 2eea265c8b6f
Create Date: 2026-02-06 17:45:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260206_174500_refactor_agent_api_keys_provider'
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

            # 6) attempt to drop the enum type if it exists
            try:
                op.execute('DROP TYPE IF EXISTS agentmodelprovider')
            except Exception:
                """Refactor agent_api_keys provider enum to relational provider_id

                Revision ID: 20260206_174500_refactor_agent_api_keys_provider
                Revises: 2eea265c8b6f
                Create Date: 2026-02-06 17:45:00.000000
                """
                from alembic import op
                import sqlalchemy as sa
                from sqlalchemy.dialects import postgresql

                # revision identifiers, used by Alembic.
                revision = '20260206_174500_refactor_agent_api_keys_provider'
                down_revision = '2eea265c8b6f'
                branch_labels = None
                depends_on = None


                def upgrade():
                    # 1) add provider_id column nullable
                    op.add_column('agent_api_keys', sa.Column('provider_id', sa.Integer(), nullable=True))
                    op.execute('CREATE INDEX IF NOT EXISTS ix_agent_api_keys_user_provider_id ON agent_api_keys (user_id, provider_id)')

                    # 2) populate provider_id using llm_key_providers.type
                    # cast enum to text for comparison
                    op.execute(
                        """
                        UPDATE agent_api_keys
                        SET provider_id = (
                            SELECT id FROM llm_key_providers WHERE llm_key_providers.type::text = agent_api_keys.provider::text LIMIT 1
                        )
                        WHERE provider IS NOT NULL
                        """
                    )

                    # 3) make provider_id non-nullable if all rows were migrated
                    op.alter_column('agent_api_keys', 'provider_id', nullable=False)

                    # 4) add foreign key constraint
                    op.create_foreign_key(
                        'agent_api_keys_provider_id_fkey',
                        'agent_api_keys', 'llm_key_providers', ['provider_id'], ['id'], ondelete='RESTRICT'
                    )

                    # 5) drop old provider enum column
                    op.drop_index('ix_agent_api_keys_user_provider', table_name='agent_api_keys')
                    op.drop_column('agent_api_keys', 'provider')

                    # 6) attempt to drop the enum type if it exists
                    try:
                        op.execute('DROP TYPE IF EXISTS agentmodelprovider')
                    except Exception:
                        # ignore if DB backend differs
                        pass


                def downgrade():
                    # Downgrade: recreate enum type and provider column, copy back values from provider_id
                    # 1) recreate enum type (best-effort: values may differ from original)
                    try:
                        op.execute("CREATE TYPE agentmodelprovider AS ENUM ('openai','anthropic','google','gemini','ollama','huggingface','azure_openai','custom','groq')")
                    except Exception:
                        pass

                    # 2) add provider enum column nullable
                    op.add_column('agent_api_keys', sa.Column('provider', postgresql.ENUM(name='agentmodelprovider'), nullable=True))

                    # 3) populate provider using llm_key_providers.type
                    op.execute(
                        """
                        UPDATE agent_api_keys
                        SET provider = (
                            SELECT llm_key_providers.type::text FROM llm_key_providers WHERE llm_key_providers.id = agent_api_keys.provider_id LIMIT 1
                        )
                        WHERE provider_id IS NOT NULL
                        """
                    )

                    # 4) drop fk and index and provider_id column
                    op.drop_constraint('agent_api_keys_provider_id_fkey', 'agent_api_keys', type_='foreignkey')
                    op.drop_index('ix_agent_api_keys_user_provider_id', table_name='agent_api_keys')
                    op.drop_column('agent_api_keys', 'provider_id')

                    # 5) recreate old index
                    op.create_index('ix_agent_api_keys_user_provider', 'agent_api_keys', ['user_id', 'provider'])