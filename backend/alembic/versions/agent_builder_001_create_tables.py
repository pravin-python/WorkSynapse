"""Create agent builder tables

Revision ID: agent_builder_001
Revises: 
Create Date: 2026-02-06 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'agent_builder_001'
down_revision = 'd41a367fd9ac'  # Updated to point to previous head
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agent_models table
    op.create_table(
        'agent_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('provider', sa.Enum(
            'openai', 'anthropic', 'google', 'gemini', 'ollama', 
            'huggingface', 'azure_openai', 'custom',
            name='agentmodelprovider'
        ), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requires_api_key', sa.Boolean(), default=True),
        sa.Column('api_key_prefix', sa.String(20), nullable=True),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('context_window', sa.Integer(), default=4096),
        sa.Column('max_output_tokens', sa.Integer(), default=4096),
        sa.Column('supports_vision', sa.Boolean(), default=False),
        sa.Column('supports_tools', sa.Boolean(), default=True),
        sa.Column('supports_streaming', sa.Boolean(), default=True),
        sa.Column('input_price_per_million', sa.Float(), default=0.0),
        sa.Column('output_price_per_million', sa.Float(), default=0.0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_deprecated', sa.Boolean(), default=False),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('deleted_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_agent_models_provider', 'agent_models', ['provider'])

    # Create agent_api_keys table
    op.create_table(
        'agent_api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.Enum(
            'openai', 'anthropic', 'google', 'gemini', 'ollama', 
            'huggingface', 'azure_openai', 'custom',
            name='agentmodelprovider'
        ), nullable=False),
        sa.Column('label', sa.String(100), nullable=False, default='default'),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('key_preview', sa.String(20), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_valid', sa.Boolean(), default=True),
        sa.Column('last_validated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('deleted_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', 'label', name='uq_agent_api_key')
    )
    op.create_index('ix_agent_api_keys_user_provider', 'agent_api_keys', ['user_id', 'provider'])

    # Create custom_agents table
    op.create_table(
        'custom_agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('model_id', sa.Integer(), sa.ForeignKey('agent_models.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('api_key_id', sa.Integer(), sa.ForeignKey('agent_api_keys.id', ondelete='SET NULL'), nullable=True),
        sa.Column('temperature', sa.Float(), default=0.7),
        sa.Column('max_tokens', sa.Integer(), default=4096),
        sa.Column('top_p', sa.Float(), default=1.0),
        sa.Column('frequency_penalty', sa.Float(), default=0.0),
        sa.Column('presence_penalty', sa.Float(), default=0.0),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('goal_prompt', sa.Text(), nullable=True),
        sa.Column('service_prompt', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum(
            'draft', 'active', 'paused', 'archived', 'error',
            name='customagentstatus'
        ), default='draft'),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('total_sessions', sa.Integer(), default=0),
        sa.Column('total_messages', sa.Integer(), default=0),
        sa.Column('total_tokens_used', sa.Integer(), default=0),
        sa.Column('total_cost_usd', sa.Float(), default=0.0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('avatar_url', sa.String(512), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('deleted_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'created_by_user_id', name='uq_custom_agent_name_user')
    )
    op.create_index('ix_custom_agents_slug', 'custom_agents', ['slug'], unique=True)
    op.create_index('ix_custom_agents_status', 'custom_agents', ['status'])
    op.create_index('ix_custom_agents_creator', 'custom_agents', ['created_by_user_id'])

    # Create agent_tools_config table
    op.create_table(
        'agent_tools_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('custom_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_type', sa.Enum(
            'github', 'slack', 'telegram', 'filesystem', 'web', 
            'email', 'database', 'api', 'custom',
            name='agenttooltype'
        ), nullable=False),
        sa.Column('tool_name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_json', sa.JSON(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('requires_auth', sa.Boolean(), default=False),
        sa.Column('is_configured', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'tool_type', name='uq_agent_tool')
    )

    # Create agent_connections table
    op.create_table(
        'agent_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('custom_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('connection_type', sa.Enum(
            'github', 'slack', 'telegram', 'jira', 'notion', 
            'discord', 'webhook', 'oauth', 'api_key',
            name='agentconnectiontype'
        ), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_json', sa.JSON(), nullable=True),
        sa.Column('encrypted_credentials', sa.Text(), nullable=True),
        sa.Column('oauth_access_token', sa.Text(), nullable=True),
        sa.Column('oauth_refresh_token', sa.Text(), nullable=True),
        sa.Column('oauth_expires_at', sa.DateTime(), nullable=True),
        sa.Column('oauth_scope', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_connected', sa.Boolean(), default=False),
        sa.Column('last_connected_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('deleted_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'connection_type', 'name', name='uq_agent_connection')
    )

    # Create agent_mcp_servers table
    op.create_table(
        'agent_mcp_servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), sa.ForeignKey('custom_agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('server_name', sa.String(100), nullable=False),
        sa.Column('server_url', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_json', sa.JSON(), nullable=True),
        sa.Column('transport_type', sa.String(50), default='stdio'),
        sa.Column('requires_auth', sa.Boolean(), default=False),
        sa.Column('auth_type', sa.String(50), nullable=True),
        sa.Column('encrypted_auth', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('is_connected', sa.Boolean(), default=False),
        sa.Column('last_health_check', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('available_tools', sa.JSON(), nullable=True),
        sa.Column('available_resources', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'server_name', name='uq_agent_mcp_server')
    )


def downgrade() -> None:
    op.drop_table('agent_mcp_servers')
    op.drop_table('agent_connections')
    op.drop_table('agent_tools_config')
    op.drop_index('ix_custom_agents_creator', 'custom_agents')
    op.drop_index('ix_custom_agents_status', 'custom_agents')
    op.drop_index('ix_custom_agents_slug', 'custom_agents')
    op.drop_table('custom_agents')
    op.drop_index('ix_agent_api_keys_user_provider', 'agent_api_keys')
    op.drop_table('agent_api_keys')
    op.drop_index('ix_agent_models_provider', 'agent_models')
    op.drop_table('agent_models')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS agentconnectiontype')
    op.execute('DROP TYPE IF EXISTS agenttooltype')
    op.execute('DROP TYPE IF EXISTS customagentstatus')
    op.execute('DROP TYPE IF EXISTS agentmodelprovider')
