"""fix_analysis_results_table_structure

Revision ID: d4b17c87ccee
Revises: c2bf04f8d306
Create Date: 2025-07-01 14:01:24.873512

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd4b17c87ccee'
down_revision = 'c2bf04f8d306'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加缺少的字段到 analysis_results 表
    op.add_column('analysis_results', sa.Column('original_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('llm_response_raw', sa.Text(), nullable=True))
    op.add_column('analysis_results', sa.Column('detected_characters', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('dialogue_segments', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('emotion_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('voice_recommendations', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('user_modifications', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('final_config', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('is_user_confirmed', sa.Boolean(), nullable=True))
    op.add_column('analysis_results', sa.Column('quality_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('analysis_results', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('analysis_results', sa.Column('confirmed_at', sa.DateTime(), nullable=True))
    
    # 修改现有字段类型
    op.alter_column('analysis_results', 'processing_time', type_=sa.Integer())
    op.alter_column('analysis_results', 'confidence_score', type_=sa.Integer())
    op.alter_column('analysis_results', 'status', type_=sa.String(20))


def downgrade() -> None:
    # 移除添加的字段
    op.drop_column('analysis_results', 'original_analysis')
    op.drop_column('analysis_results', 'llm_response_raw')
    op.drop_column('analysis_results', 'detected_characters')
    op.drop_column('analysis_results', 'dialogue_segments')
    op.drop_column('analysis_results', 'emotion_analysis')
    op.drop_column('analysis_results', 'voice_recommendations')
    op.drop_column('analysis_results', 'user_modifications')
    op.drop_column('analysis_results', 'final_config')
    op.drop_column('analysis_results', 'is_user_confirmed')
    op.drop_column('analysis_results', 'quality_metrics')
    op.drop_column('analysis_results', 'completed_at')
    op.drop_column('analysis_results', 'confirmed_at') 