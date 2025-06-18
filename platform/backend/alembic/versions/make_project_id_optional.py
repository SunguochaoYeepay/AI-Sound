"""make project_id and session_id optional

Revision ID: make_project_optional
Revises: 20250618_add_color_to_categories
Create Date: 2025-06-18 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'make_project_optional'
down_revision = '20250618_add_color_to_categories'
branch_labels = None
depends_on = None


def upgrade():
    """Make project_id in analysis_sessions and session_id in analysis_results nullable"""
    
    # 修改 analysis_sessions 表，使 project_id 可选
    op.alter_column('analysis_sessions', 'project_id',
                   existing_type=sa.INTEGER(),
                   nullable=True)
    
    # 修改 analysis_results 表，使 session_id 可选  
    op.alter_column('analysis_results', 'session_id',
                   existing_type=sa.INTEGER(),
                   nullable=True)


def downgrade():
    """Revert project_id and session_id to be required"""
    
    # 恢复 analysis_results 表，使 session_id 必需
    op.alter_column('analysis_results', 'session_id',
                   existing_type=sa.INTEGER(),
                   nullable=False)
    
    # 恢复 analysis_sessions 表，使 project_id 必需
    op.alter_column('analysis_sessions', 'project_id',
                   existing_type=sa.INTEGER(),
                   nullable=False) 