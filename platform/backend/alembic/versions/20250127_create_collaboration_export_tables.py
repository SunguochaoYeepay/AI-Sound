"""create collaboration and export tables

Revision ID: 20250127_create_collaboration_export_tables
Revises: 20250127_create_audio_editor_tables
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250127_create_collaboration_export_tables'
down_revision = '20250127_create_audio_editor_tables'
branch_labels = None
depends_on = None


def upgrade():
    # 项目模板表
    op.create_table('project_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('preview_image', sa.String(500), nullable=True),
        sa.Column('config_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_project_templates_category', 'project_templates', ['category'])
    op.create_index('ix_project_templates_is_public', 'project_templates', ['is_public'])

    # 编辑历史记录表
    op.create_table('edit_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('operation_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('snapshot_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['audio_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_edit_history_project_id', 'edit_history', ['project_id'])
    op.create_index('ix_edit_history_version_number', 'edit_history', ['version_number'])

    # 导出任务表
    op.create_table('export_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('export_format', sa.String(20), nullable=False),
        sa.Column('export_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, default=0),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['audio_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_export_tasks_project_id', 'export_tasks', ['project_id'])
    op.create_index('ix_export_tasks_status', 'export_tasks', ['status'])

    # 项目分享表
    op.create_table('project_shares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('share_token', sa.String(64), nullable=False, unique=True),
        sa.Column('share_type', sa.String(20), nullable=False, default='view'),
        sa.Column('password', sa.String(255), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['audio_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_project_shares_share_token', 'project_shares', ['share_token'])
    op.create_index('ix_project_shares_project_id', 'project_shares', ['project_id'])

    # 云端同步状态表
    op.create_table('sync_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('local_version', sa.Integer(), nullable=False, default=1),
        sa.Column('cloud_version', sa.Integer(), nullable=False, default=0),
        sa.Column('sync_status', sa.String(20), nullable=False, default='local'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('sync_error', sa.Text(), nullable=True),
        sa.Column('cloud_storage_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['audio_projects.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_sync_status_project_id', 'sync_status', ['project_id'])
    op.create_index('ix_sync_status_sync_status', 'sync_status', ['sync_status'])


def downgrade():
    op.drop_table('sync_status')
    op.drop_table('project_shares')
    op.drop_table('export_tasks')
    op.drop_table('edit_history')
    op.drop_table('project_templates') 