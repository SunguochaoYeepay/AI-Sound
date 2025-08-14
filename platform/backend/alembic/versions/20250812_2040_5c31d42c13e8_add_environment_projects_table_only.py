"""add_environment_projects_table_only

Revision ID: 5c31d42c13e8
Revises: 20250202_add_character_consistency_fields
Create Date: 2025-08-12 20:40:51.889969

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c31d42c13e8'
down_revision = '20250202_add_character_consistency_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建环境音效项目表
    op.create_table('environment_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('analysis_result', sa.JSON(), nullable=True),
        sa.Column('matching_result', sa.JSON(), nullable=True),
        sa.Column('chapter_ids', sa.JSON(), nullable=True),
        sa.Column('analysis_options', sa.JSON(), nullable=True),
        sa.Column('analysis_tracks', sa.Integer(), nullable=True),
        sa.Column('generation_count', sa.Integer(), nullable=True),
        sa.Column('matched_count', sa.Integer(), nullable=True),
        sa.Column('book_name', sa.String(length=255), nullable=True),
        sa.Column('chapter_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environment_projects_id'), 'environment_projects', ['id'], unique=False)


def downgrade() -> None:
    # 删除环境音效项目表
    op.drop_index(op.f('ix_environment_projects_id'), table_name='environment_projects')
    op.drop_table('environment_projects') 