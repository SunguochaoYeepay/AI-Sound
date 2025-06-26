"""create environment generation tables

Revision ID: 20250125_env_gen_001
Revises: 
Create Date: 2025-01-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250125_env_gen_001'
down_revision = None  # 这里应该设置为最新的revision ID
branch_labels = None
depends_on = None


def upgrade():
    # 创建环境音生成会话表
    op.create_table('environment_generation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.String(length=50), nullable=False),
        sa.Column('session_status', sa.String(length=20), nullable=True),
        sa.Column('analysis_result', sa.JSON(), nullable=True),
        sa.Column('analysis_stats', sa.JSON(), nullable=True),
        sa.Column('analysis_timestamp', sa.DateTime(), nullable=True),
        sa.Column('validation_data', sa.JSON(), nullable=True),
        sa.Column('validation_summary', sa.JSON(), nullable=True),
        sa.Column('validation_timestamp', sa.DateTime(), nullable=True),
        sa.Column('persistence_data', sa.JSON(), nullable=True),
        sa.Column('persistence_summary', sa.JSON(), nullable=True),
        sa.Column('persistence_timestamp', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environment_generation_sessions_chapter_id'), 'environment_generation_sessions', ['chapter_id'], unique=False)
    op.create_index(op.f('ix_environment_generation_sessions_id'), 'environment_generation_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_environment_generation_sessions_project_id'), 'environment_generation_sessions', ['project_id'], unique=False)
    op.create_index(op.f('ix_environment_generation_sessions_session_status'), 'environment_generation_sessions', ['session_status'], unique=False)
    
    # 创建环境音轨道配置表
    op.create_table('environment_track_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('segment_id', sa.String(length=50), nullable=False),
        sa.Column('track_index', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('scene_description', sa.Text(), nullable=True),
        sa.Column('environment_keywords', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('inheritance_applied', sa.Boolean(), nullable=True),
        sa.Column('inherited_environment', sa.JSON(), nullable=True),
        sa.Column('previous_track_id', sa.Integer(), nullable=True),
        sa.Column('manual_edits', sa.JSON(), nullable=True),
        sa.Column('validation_status', sa.String(length=20), nullable=True),
        sa.Column('validation_notes', sa.Text(), nullable=True),
        sa.Column('validation_timestamp', sa.DateTime(), nullable=True),
        sa.Column('matching_suggestions', sa.JSON(), nullable=True),
        sa.Column('selected_tangoflux_config', sa.JSON(), nullable=True),
        sa.Column('final_prompt', sa.Text(), nullable=True),
        sa.Column('fade_in', sa.Float(), nullable=True),
        sa.Column('fade_out', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('loop_enabled', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['previous_track_id'], ['environment_track_configs.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['environment_generation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environment_track_configs_id'), 'environment_track_configs', ['id'], unique=False)
    op.create_index(op.f('ix_environment_track_configs_segment_id'), 'environment_track_configs', ['segment_id'], unique=False)
    op.create_index(op.f('ix_environment_track_configs_session_id'), 'environment_track_configs', ['session_id'], unique=False)
    
    # 创建环境音混合任务表
    op.create_table('environment_audio_mixing_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.String(length=50), nullable=False),
        sa.Column('job_status', sa.String(length=20), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('mixing_config', sa.JSON(), nullable=True),
        sa.Column('total_tracks', sa.Integer(), nullable=True),
        sa.Column('completed_tracks', sa.Integer(), nullable=True),
        sa.Column('failed_tracks', sa.Integer(), nullable=True),
        sa.Column('output_file_path', sa.String(length=500), nullable=True),
        sa.Column('output_duration', sa.Float(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['environment_generation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environment_audio_mixing_jobs_chapter_id'), 'environment_audio_mixing_jobs', ['chapter_id'], unique=False)
    op.create_index(op.f('ix_environment_audio_mixing_jobs_id'), 'environment_audio_mixing_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_environment_audio_mixing_jobs_job_status'), 'environment_audio_mixing_jobs', ['job_status'], unique=False)
    op.create_index(op.f('ix_environment_audio_mixing_jobs_project_id'), 'environment_audio_mixing_jobs', ['project_id'], unique=False)
    op.create_index(op.f('ix_environment_audio_mixing_jobs_session_id'), 'environment_audio_mixing_jobs', ['session_id'], unique=False)
    
    # 创建环境音生成日志表
    op.create_table('environment_generation_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('log_level', sa.String(length=10), nullable=False),
        sa.Column('log_message', sa.Text(), nullable=False),
        sa.Column('log_details', sa.JSON(), nullable=True),
        sa.Column('operation', sa.String(length=50), nullable=True),
        sa.Column('user_id', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['environment_generation_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environment_generation_logs_id'), 'environment_generation_logs', ['id'], unique=False)
    op.create_index(op.f('ix_environment_generation_logs_log_level'), 'environment_generation_logs', ['log_level'], unique=False)
    op.create_index(op.f('ix_environment_generation_logs_operation'), 'environment_generation_logs', ['operation'], unique=False)
    op.create_index(op.f('ix_environment_generation_logs_session_id'), 'environment_generation_logs', ['session_id'], unique=False)


def downgrade():
    # 删除所有表和索引
    op.drop_index(op.f('ix_environment_generation_logs_session_id'), table_name='environment_generation_logs')
    op.drop_index(op.f('ix_environment_generation_logs_operation'), table_name='environment_generation_logs')
    op.drop_index(op.f('ix_environment_generation_logs_log_level'), table_name='environment_generation_logs')
    op.drop_index(op.f('ix_environment_generation_logs_id'), table_name='environment_generation_logs')
    op.drop_table('environment_generation_logs')
    
    op.drop_index(op.f('ix_environment_audio_mixing_jobs_session_id'), table_name='environment_audio_mixing_jobs')
    op.drop_index(op.f('ix_environment_audio_mixing_jobs_project_id'), table_name='environment_audio_mixing_jobs')
    op.drop_index(op.f('ix_environment_audio_mixing_jobs_job_status'), table_name='environment_audio_mixing_jobs')
    op.drop_index(op.f('ix_environment_audio_mixing_jobs_id'), table_name='environment_audio_mixing_jobs')
    op.drop_index(op.f('ix_environment_audio_mixing_jobs_chapter_id'), table_name='environment_audio_mixing_jobs')
    op.drop_table('environment_audio_mixing_jobs')
    
    op.drop_index(op.f('ix_environment_track_configs_session_id'), table_name='environment_track_configs')
    op.drop_index(op.f('ix_environment_track_configs_segment_id'), table_name='environment_track_configs')
    op.drop_index(op.f('ix_environment_track_configs_id'), table_name='environment_track_configs')
    op.drop_table('environment_track_configs')
    
    op.drop_index(op.f('ix_environment_generation_sessions_session_status'), table_name='environment_generation_sessions')
    op.drop_index(op.f('ix_environment_generation_sessions_project_id'), table_name='environment_generation_sessions')
    op.drop_index(op.f('ix_environment_generation_sessions_id'), table_name='environment_generation_sessions')
    op.drop_index(op.f('ix_environment_generation_sessions_chapter_id'), table_name='environment_generation_sessions')
    op.drop_table('environment_generation_sessions') 