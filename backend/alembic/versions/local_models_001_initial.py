"""Create local models tables

Revision ID: local_models_001
Revises: agent_builder_001
Create Date: 2026-02-06 01:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'local_models_001'
down_revision = 'agent_builder_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create local_models table
    op.create_table(
        'local_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('model_id', sa.String(500), nullable=False),
        sa.Column('source', sa.Enum(
            'huggingface', 'ollama', 'custom',
            name='modelsource'
        ), nullable=False),
        sa.Column('model_type', sa.Enum(
            'text-generation', 'text2text-generation', 'chat', 'embedding',
            'image-generation', 'audio', 'multimodal', 'other',
            name='modeltype'
        ), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('version', sa.String(100), nullable=True),
        sa.Column('license', sa.String(100), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('local_path', sa.String(1000), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum(
            'pending', 'downloading', 'ready', 'failed', 'cancelled',
            name='modelstatus'
        ), nullable=False),
        sa.Column('progress', sa.Float(), default=0.0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('task_id', sa.String(255), nullable=True),
        sa.Column('downloaded_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('download_started_at', sa.DateTime(), nullable=True),
        sa.Column('download_completed_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('default_params', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        # Audit fields
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('deleted_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id')
    )
    
    op.create_index(
        'ix_local_models_source_status', 
        'local_models', 
        ['source', 'status']
    )
    op.create_index(
        'ix_local_models_model_id', 
        'local_models', 
        ['model_id']
    )

    # Create model_download_logs table
    op.create_table(
        'model_download_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_id', sa.Integer(), sa.ForeignKey('local_models.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('bytes_downloaded', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        # Audit fields
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('deleted_by_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('model_download_logs')
    op.drop_index('ix_local_models_model_id', 'local_models')
    op.drop_index('ix_local_models_source_status', 'local_models')
    op.drop_table('local_models')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS modelsource')
    op.execute('DROP TYPE IF EXISTS modelstatus')
    op.execute('DROP TYPE IF EXISTS modeltype')
