"""create analysis tables

Revision ID: 20250618_create_analysis
Create Date: 2025-06-18 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '20250618_create_analysis'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analysis_sessions table
    op.create_table(
        'analysis_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('book_id', sa.Integer(), nullable=True),
        sa.Column('target_type', sa.String(20), nullable=False),
        sa.Column('target_ids', sa.Text(), nullable=True),
        sa.Column('llm_provider', sa.String(50), server_default='dify', nullable=True),
        sa.Column('llm_model', sa.String(100), nullable=True),
        sa.Column('llm_workflow_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), server_default='pending', nullable=True),
        sa.Column('progress', sa.Integer(), server_default='0', nullable=True),
        sa.Column('current_processing', sa.Text(), nullable=True),
        sa.Column('total_tasks', sa.Integer(), server_default='0', nullable=True),
        sa.Column('completed_tasks', sa.Integer(), server_default='0', nullable=True),
        sa.Column('failed_tasks', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['project_id'], ['novel_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['book_id'], ['books.id'], ondelete='SET NULL')
    )

    # Create analysis_results table
    op.create_table(
        'analysis_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('input_text', sa.Text(), nullable=False),
        sa.Column('input_hash', sa.String(64), nullable=True),
        sa.Column('llm_request_id', sa.String(100), nullable=True),
        sa.Column('llm_response_time', sa.Integer(), nullable=True),
        sa.Column('raw_response', JSONB(), nullable=True),
        sa.Column('project_info', JSONB(), nullable=True),
        sa.Column('synthesis_plan', JSONB(), nullable=False),
        sa.Column('characters', JSONB(), nullable=False),
        sa.Column('user_modified', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('user_config', JSONB(), nullable=True),
        sa.Column('final_config', JSONB(), nullable=True),
        sa.Column('status', sa.String(20), server_default='active', nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('applied_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['analysis_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chapter_id'], ['book_chapters.id'], ondelete='SET NULL')
    )

    # Create indexes
    op.create_index('idx_session_chapter', 'analysis_results', ['session_id', 'chapter_id'])
    op.create_index('idx_input_hash', 'analysis_results', ['input_hash'])
    op.create_index('idx_status_version', 'analysis_results', ['status', 'version'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_status_version', table_name='analysis_results')
    op.drop_index('idx_input_hash', table_name='analysis_results')
    op.drop_index('idx_session_chapter', table_name='analysis_results')

    # Drop tables
    op.drop_table('analysis_results')
    op.drop_table('analysis_sessions') 