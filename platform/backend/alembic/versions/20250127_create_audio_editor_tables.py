"""Create audio editor tables

Revision ID: 20250127_create_audio_editor_tables
Revises: 20250125_add_environment_sound_id_to_tracks
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250127_create_audio_editor_tables'
down_revision = '20250125_add_environment_sound_id_to_tracks'
branch_labels = None
depends_on = None


def upgrade():
    # 创建音视频项目表
    op.create_table(
        'audio_video_projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_project_id', sa.Integer(), nullable=True),
        sa.Column('project_type', sa.String(50), nullable=False, default='audio_editing'),
        sa.Column('status', sa.String(50), nullable=False, default='draft'),
        sa.Column('project_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('total_duration', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 添加外键约束到novel_projects表
    op.create_foreign_key(
        'fk_audio_video_projects_source_project_id',
        'audio_video_projects', 'novel_projects',
        ['source_project_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 创建索引
    op.create_index('ix_audio_video_projects_name', 'audio_video_projects', ['name'])
    op.create_index('ix_audio_video_projects_status', 'audio_video_projects', ['status'])
    op.create_index('ix_audio_video_projects_created_at', 'audio_video_projects', ['created_at'])

    # 创建编辑轨道表
    op.create_table(
        'editor_tracks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('track_name', sa.String(255), nullable=False),
        sa.Column('track_type', sa.String(50), nullable=False),  # dialogue, environment, effects, music
        sa.Column('track_order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_muted', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_solo', sa.Boolean(), nullable=False, default=False),
        sa.Column('volume', sa.Float(), nullable=False, default=1.0),
        sa.Column('pan', sa.Float(), nullable=False, default=0.0),  # -1.0 (左) 到 1.0 (右)
        sa.Column('track_color', sa.String(7), nullable=True),  # HEX颜色值
        sa.Column('track_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 编辑轨道外键约束
    op.create_foreign_key(
        'fk_editor_tracks_project_id',
        'editor_tracks', 'audio_video_projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 编辑轨道索引
    op.create_index('ix_editor_tracks_project_id', 'editor_tracks', ['project_id'])
    op.create_index('ix_editor_tracks_track_order', 'editor_tracks', ['track_order'])

    # 创建音频片段表
    op.create_table(
        'audio_clips',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('track_id', sa.Integer(), nullable=False),
        sa.Column('clip_name', sa.String(255), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('original_file_path', sa.String(500), nullable=True),  # 原始文件路径
        sa.Column('start_time', sa.Float(), nullable=False),  # 在时间轴上的开始时间
        sa.Column('end_time', sa.Float(), nullable=False),    # 在时间轴上的结束时间
        sa.Column('source_start', sa.Float(), nullable=False, default=0.0),  # 源文件裁剪开始点
        sa.Column('source_end', sa.Float(), nullable=True),   # 源文件裁剪结束点
        sa.Column('volume', sa.Float(), nullable=False, default=1.0),
        sa.Column('fade_in', sa.Float(), nullable=False, default=0.0),   # 淡入时长
        sa.Column('fade_out', sa.Float(), nullable=False, default=0.0),  # 淡出时长
        sa.Column('effects', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('clip_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 音频片段外键约束
    op.create_foreign_key(
        'fk_audio_clips_track_id',
        'audio_clips', 'editor_tracks',
        ['track_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 音频片段索引
    op.create_index('ix_audio_clips_track_id', 'audio_clips', ['track_id'])
    op.create_index('ix_audio_clips_start_time', 'audio_clips', ['start_time'])
    op.create_index('ix_audio_clips_end_time', 'audio_clips', ['end_time'])

    # 创建编辑器设置表（存储用户偏好设置）
    op.create_table(
        'editor_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('zoom_level', sa.Float(), nullable=False, default=1.0),
        sa.Column('playhead_position', sa.Float(), nullable=False, default=0.0),
        sa.Column('visible_tracks', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('timeline_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ui_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 编辑器设置外键约束
    op.create_foreign_key(
        'fk_editor_settings_project_id',
        'editor_settings', 'audio_video_projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 编辑器设置索引
    op.create_index('ix_editor_settings_project_id', 'editor_settings', ['project_id'])

    # 创建渲染任务表（用于后台音频处理任务）
    op.create_table(
        'render_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),  # preview, export, mix
        sa.Column('task_status', sa.String(50), nullable=False, default='pending'),  # pending, processing, completed, failed
        sa.Column('progress', sa.Float(), nullable=False, default=0.0),
        sa.Column('task_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('result_file_path', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 渲染任务外键约束
    op.create_foreign_key(
        'fk_render_tasks_project_id',
        'render_tasks', 'audio_video_projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # 渲染任务索引
    op.create_index('ix_render_tasks_project_id', 'render_tasks', ['project_id'])
    op.create_index('ix_render_tasks_status', 'render_tasks', ['task_status'])
    op.create_index('ix_render_tasks_created_at', 'render_tasks', ['created_at'])


def downgrade():
    # 删除表（按照依赖关系倒序删除）
    op.drop_table('render_tasks')
    op.drop_table('editor_settings')
    op.drop_table('audio_clips')
    op.drop_table('editor_tracks')
    op.drop_table('audio_video_projects') 