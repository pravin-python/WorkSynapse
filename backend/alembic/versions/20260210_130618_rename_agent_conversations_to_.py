"""rename agent_conversations to orchestrator_conversations

Revision ID: ef9851773ef1
Revises: 3f590ac33ab4
Create Date: 2026-02-10 13:06:18.440382+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ef9851773ef1'
down_revision: Union[str, None] = '3f590ac33ab4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create orchestrator_agents table
    op.create_table(
        'orchestrator_agents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('identity_guidance', sa.Text(), nullable=True),
        sa.Column('llm_provider', sa.String(length=50), nullable=False, server_default='openai'),
        sa.Column('model_name', sa.String(length=100), nullable=False, server_default='gpt-4o'),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='4096'),
        sa.Column('tools', postgresql.JSONB(), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=False, server_default='conversation'),
        sa.Column('enable_long_term_memory', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('memory_config', postgresql.JSONB(), nullable=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=True),
        sa.Column('config', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enable_planning', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enable_reasoning', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_stop_itself', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_orchestrator_agents_name', 'orchestrator_agents', ['name'])

    # 2. Create orchestrator_conversations table
    op.create_table(
        'orchestrator_conversations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('messages', postgresql.JSONB(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['orchestrator_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('thread_id'),
    )
    op.create_index('ix_orch_conv_agent_id', 'orchestrator_conversations', ['agent_id'])
    op.create_index('ix_orch_conv_user_id', 'orchestrator_conversations', ['user_id'])
    op.create_index('ix_orch_conv_thread_id', 'orchestrator_conversations', ['thread_id'])

    # 3. Create agent_executions table
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('input_message', sa.Text(), nullable=False),
        sa.Column('output_message', sa.Text(), nullable=True),
        sa.Column('tool_calls', postgresql.JSONB(), nullable=True),
        sa.Column('tokens_input', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_output', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tokens_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['orchestrator_agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['orchestrator_conversations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_exec_agent_id', 'agent_executions', ['agent_id'])
    op.create_index('ix_agent_exec_user_id', 'agent_executions', ['user_id'])
    op.create_index('ix_agent_exec_status', 'agent_executions', ['status'])


def downgrade() -> None:
    op.drop_index('ix_agent_exec_status', 'agent_executions')
    op.drop_index('ix_agent_exec_user_id', 'agent_executions')
    op.drop_index('ix_agent_exec_agent_id', 'agent_executions')
    op.drop_table('agent_executions')

    op.drop_index('ix_orch_conv_thread_id', 'orchestrator_conversations')
    op.drop_index('ix_orch_conv_user_id', 'orchestrator_conversations')
    op.drop_index('ix_orch_conv_agent_id', 'orchestrator_conversations')
    op.drop_table('orchestrator_conversations')

    op.drop_index('ix_orchestrator_agents_name', 'orchestrator_agents')
    op.drop_table('orchestrator_agents')
