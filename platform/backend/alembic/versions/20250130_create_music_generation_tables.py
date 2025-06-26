"""创建音乐生成相关数据库表

Revision ID: 20250130_music_generation
Revises: 20250129_create_background_music_tables
Create Date: 2025-01-30 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '20250130_music_generation'
down_revision = '20250129_create_background_music_tables'
branch_labels = None
depends_on = None


def upgrade():
    """创建音乐生成相关数据库表"""
    
    # 创建枚举类型
    music_generation_status = sa.Enum(
        'pending', 'processing', 'completed', 'failed', 'cancelled',
        name='musicgenerationstatus'
    )
    music_scene_type = sa.Enum(
        'battle', 'romance', 'mystery', 'peaceful', 'sad', 'custom',
        name='musicscenetype'
    )
    fade_mode = sa.Enum(
        'standard', 'smooth', 'quick',
        name='fademode'
    )
    
    # 创建枚举类型（如果不存在）
    try:
        music_generation_status.create(op.get_bind())
    except:
        pass
    try:
        music_scene_type.create(op.get_bind())
    except:
        pass
    try:
        fade_mode.create(op.get_bind())
    except:
        pass
    
    # 1. 音乐生成任务表
    op.create_table(
        'music_generation_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        
        # 任务基本信息
        sa.Column('task_id', sa.String(length=64), nullable=False, comment='任务唯一标识'),
        sa.Column('chapter_id', sa.String(length=64), nullable=True, comment='关联章节ID'),
        sa.Column('novel_project_id', sa.Integer(), nullable=True, comment='关联小说项目ID'),
        
        # 生成参数
        sa.Column('content', sa.Text(), nullable=False, comment='生成音乐的文本内容'),
        sa.Column('target_duration', sa.Integer(), nullable=True, default=30, comment='目标时长（秒）'),
        sa.Column('custom_style', sa.String(length=100), nullable=True, comment='自定义音乐风格'),
        sa.Column('volume_level', sa.Float(), nullable=True, default=-12.0, comment='音量等级（dB）'),
        sa.Column('fade_mode', fade_mode, nullable=True, default='standard', comment='淡入淡出模式'),
        sa.Column('fade_in', sa.Float(), nullable=True, default=2.0, comment='淡入时间（秒）'),
        sa.Column('fade_out', sa.Float(), nullable=True, default=2.0, comment='淡出时间（秒）'),
        
        # 任务状态
        sa.Column('status', music_generation_status, nullable=True, default='pending', comment='任务状态'),
        sa.Column('progress', sa.Float(), nullable=True, default=0.0, comment='任务进度（0.0-1.0）'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        
        # 生成结果
        sa.Column('audio_path', sa.String(length=500), nullable=True, comment='生成的音频文件路径'),
        sa.Column('audio_url', sa.String(length=500), nullable=True, comment='音频访问URL'),
        sa.Column('actual_duration', sa.Float(), nullable=True, comment='实际音频时长（秒）'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        
        # 性能指标
        sa.Column('generation_time', sa.Float(), nullable=True, comment='生成耗时（秒）'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        
        # 用户信息
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('user_preferences', sa.JSON(), nullable=True, comment='用户偏好设置'),
        
        sa.ForeignKeyConstraint(['novel_project_id'], ['novel_projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id')
    )
    
    # 创建索引
    op.create_index('ix_music_generation_tasks_task_id', 'music_generation_tasks', ['task_id'])
    op.create_index('ix_music_generation_tasks_chapter_id', 'music_generation_tasks', ['chapter_id'])
    op.create_index('ix_music_generation_tasks_status', 'music_generation_tasks', ['status'])
    op.create_index('ix_music_generation_tasks_user_id', 'music_generation_tasks', ['user_id'])
    
    # 2. 音乐场景分析表
    op.create_table(
        'music_scene_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        
        # 关联任务
        sa.Column('generation_task_id', sa.Integer(), nullable=False, comment='关联生成任务ID'),
        
        # 场景分析结果
        sa.Column('primary_scene_type', music_scene_type, nullable=False, comment='主要场景类型'),
        sa.Column('emotion_tone', sa.String(length=100), nullable=False, comment='情绪基调'),
        sa.Column('intensity', sa.Float(), nullable=False, comment='强度（0.0-1.0）'),
        sa.Column('confidence', sa.Float(), nullable=False, comment='置信度（0.0-1.0）'),
        
        # 分析详情
        sa.Column('keywords', sa.JSON(), nullable=True, comment='关键词列表'),
        sa.Column('secondary_scenes', sa.JSON(), nullable=True, comment='次要场景信息'),
        sa.Column('transition_points', sa.JSON(), nullable=True, comment='场景转换点'),
        
        # 音乐建议
        sa.Column('overall_mood', sa.String(length=100), nullable=True, comment='整体氛围'),
        sa.Column('tempo_preference', sa.Integer(), nullable=True, comment='节奏偏好（BPM）'),
        sa.Column('volume_suggestion', sa.Float(), nullable=True, comment='音量建议（dB）'),
        sa.Column('duration_hint', sa.Integer(), nullable=True, comment='时长建议（秒）'),
        
        # 风格推荐
        sa.Column('style_recommendations', sa.JSON(), nullable=True, comment='风格推荐列表'),
        
        # 分析元数据
        sa.Column('content_length', sa.Integer(), nullable=True, comment='分析文本长度'),
        sa.Column('analysis_version', sa.String(length=20), nullable=True, default='1.0', comment='分析算法版本'),
        sa.Column('analysis_time', sa.Float(), nullable=True, comment='分析耗时（秒）'),
        
        sa.ForeignKeyConstraint(['generation_task_id'], ['music_generation_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 3. 生成的音乐文件表
    op.create_table(
        'generated_music_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        
        # 关联任务
        sa.Column('generation_task_id', sa.Integer(), nullable=False, comment='关联生成任务ID'),
        
        # 文件信息
        sa.Column('filename', sa.String(length=255), nullable=False, comment='文件名'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='文件路径'),
        sa.Column('file_url', sa.String(length=500), nullable=True, comment='访问URL'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('file_format', sa.String(length=10), nullable=True, default='wav', comment='文件格式'),
        
        # 音频属性
        sa.Column('duration', sa.Float(), nullable=True, comment='音频时长（秒）'),
        sa.Column('sample_rate', sa.Integer(), nullable=True, comment='采样率'),
        sa.Column('bit_depth', sa.Integer(), nullable=True, comment='位深度'),
        sa.Column('channels', sa.Integer(), nullable=True, default=2, comment='声道数'),
        
        # 音乐属性
        sa.Column('volume_level', sa.Float(), nullable=True, comment='音量等级（dB）'),
        sa.Column('tempo', sa.Integer(), nullable=True, comment='节奏（BPM）'),
        sa.Column('key_signature', sa.String(length=10), nullable=True, comment='调性'),
        
        # 质量评估
        sa.Column('quality_score', sa.Float(), nullable=True, comment='质量评分（0.0-1.0）'),
        sa.Column('noise_level', sa.Float(), nullable=True, comment='噪音水平'),
        sa.Column('dynamic_range', sa.Float(), nullable=True, comment='动态范围'),
        
        # 使用统计
        sa.Column('download_count', sa.Integer(), nullable=True, default=0, comment='下载次数'),
        sa.Column('play_count', sa.Integer(), nullable=True, default=0, comment='播放次数'),
        sa.Column('last_accessed', sa.DateTime(), nullable=True, comment='最后访问时间'),
        
        # 状态管理
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True, comment='是否可用'),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False, comment='是否公开'),
        
        sa.ForeignKeyConstraint(['generation_task_id'], ['music_generation_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 4. 音乐生成批处理表
    op.create_table(
        'music_generation_batches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        
        # 批处理信息
        sa.Column('batch_id', sa.String(length=64), nullable=False, comment='批处理唯一标识'),
        sa.Column('batch_name', sa.String(length=200), nullable=True, comment='批处理名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='批处理描述'),
        
        # 批处理参数
        sa.Column('total_chapters', sa.Integer(), nullable=False, comment='总章节数'),
        sa.Column('default_duration', sa.Integer(), nullable=True, default=30, comment='默认时长（秒）'),
        sa.Column('default_volume_level', sa.Float(), nullable=True, default=-12.0, comment='默认音量等级（dB）'),
        sa.Column('max_concurrent', sa.Integer(), nullable=True, default=2, comment='最大并发数'),
        
        # 批处理状态
        sa.Column('status', sa.String(length=20), nullable=True, default='pending', comment='批处理状态'),
        sa.Column('success_count', sa.Integer(), nullable=True, default=0, comment='成功数量'),
        sa.Column('failed_count', sa.Integer(), nullable=True, default=0, comment='失败数量'),
        sa.Column('progress', sa.Float(), nullable=True, default=0.0, comment='整体进度（0.0-1.0）'),
        
        # 时间记录
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('estimated_completion', sa.DateTime(), nullable=True, comment='预计完成时间'),
        
        # 用户信息
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('novel_project_id', sa.Integer(), nullable=True, comment='关联小说项目ID'),
        
        # 配置和结果
        sa.Column('batch_config', sa.JSON(), nullable=True, comment='批处理配置'),
        sa.Column('batch_results', sa.JSON(), nullable=True, comment='批处理结果'),
        sa.Column('error_summary', sa.JSON(), nullable=True, comment='错误汇总'),
        
        sa.ForeignKeyConstraint(['novel_project_id'], ['novel_projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_id')
    )
    
    # 创建索引
    op.create_index('ix_music_generation_batches_batch_id', 'music_generation_batches', ['batch_id'])
    
    # 5. 音乐风格模板表
    op.create_table(
        'music_style_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        
        # 模板基本信息
        sa.Column('name', sa.String(length=100), nullable=False, comment='风格名称'),
        sa.Column('display_name', sa.String(length=100), nullable=False, comment='显示名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='风格描述'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='风格分类'),
        
        # 风格参数
        sa.Column('default_tempo', sa.Integer(), nullable=True, comment='默认节奏（BPM）'),
        sa.Column('tempo_range_min', sa.Integer(), nullable=True, comment='节奏范围最小值'),
        sa.Column('tempo_range_max', sa.Integer(), nullable=True, comment='节奏范围最大值'),
        sa.Column('default_volume', sa.Float(), nullable=True, comment='默认音量（dB）'),
        sa.Column('volume_range_min', sa.Float(), nullable=True, comment='音量范围最小值'),
        sa.Column('volume_range_max', sa.Float(), nullable=True, comment='音量范围最大值'),
        sa.Column('default_intensity', sa.Float(), nullable=True, comment='默认强度'),
        sa.Column('intensity_range_min', sa.Float(), nullable=True, comment='强度范围最小值'),
        sa.Column('intensity_range_max', sa.Float(), nullable=True, comment='强度范围最大值'),
        
        # 风格特征
        sa.Column('keywords', sa.JSON(), nullable=True, comment='关键词列表'),
        sa.Column('emotion_tags', sa.JSON(), nullable=True, comment='情绪标签'),
        sa.Column('scene_types', sa.JSON(), nullable=True, comment='适用场景类型'),
        
        # 生成参数
        sa.Column('generation_params', sa.JSON(), nullable=True, comment='生成参数配置'),
        sa.Column('post_processing_params', sa.JSON(), nullable=True, comment='后处理参数'),
        
        # 使用统计
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0, comment='使用次数'),
        sa.Column('success_rate', sa.Float(), nullable=True, comment='成功率'),
        sa.Column('average_rating', sa.Float(), nullable=True, comment='平均评分'),
        
        # 状态管理
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True, comment='是否启用'),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=False, comment='是否系统内置'),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=True, comment='是否公开'),
        
        # 创建者信息
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建者ID'),
        
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # 6. 音乐生成使用日志表
    op.create_table(
        'music_generation_usage_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        
        # 关联信息
        sa.Column('task_id', sa.String(length=64), nullable=False, comment='任务ID'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        
        # 使用详情
        sa.Column('action', sa.String(length=50), nullable=False, comment='操作类型'),
        sa.Column('content_length', sa.Integer(), nullable=True, comment='内容长度'),
        sa.Column('generation_duration', sa.Float(), nullable=True, comment='生成时长（秒）'),
        
        # 参数记录
        sa.Column('style_used', sa.String(length=100), nullable=True, comment='使用的风格'),
        sa.Column('target_duration', sa.Integer(), nullable=True, comment='目标时长'),
        sa.Column('volume_level', sa.Float(), nullable=True, comment='音量等级'),
        
        # 结果记录
        sa.Column('success', sa.Boolean(), nullable=False, comment='是否成功'),
        sa.Column('error_code', sa.String(length=50), nullable=True, comment='错误代码'),
        sa.Column('quality_score', sa.Float(), nullable=True, comment='质量评分'),
        
        # 系统信息
        sa.Column('api_version', sa.String(length=20), nullable=True, comment='API版本'),
        sa.Column('client_info', sa.JSON(), nullable=True, comment='客户端信息'),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_music_generation_usage_logs_task_id', 'music_generation_usage_logs', ['task_id'])
    
    # 7. 音乐生成系统设置表
    op.create_table(
        'music_generation_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True, comment='更新时间'),
        
        # 设置基本信息
        sa.Column('setting_key', sa.String(length=100), nullable=False, comment='设置键名'),
        sa.Column('setting_value', sa.Text(), nullable=True, comment='设置值'),
        sa.Column('setting_type', sa.String(length=20), nullable=True, default='string', comment='设置类型'),
        
        # 设置描述
        sa.Column('display_name', sa.String(length=200), nullable=True, comment='显示名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='设置描述'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='设置分类'),
        
        # 验证规则
        sa.Column('validation_rules', sa.JSON(), nullable=True, comment='验证规则'),
        sa.Column('default_value', sa.Text(), nullable=True, comment='默认值'),
        
        # 状态管理
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True, comment='是否启用'),
        sa.Column('is_system', sa.Boolean(), nullable=True, default=False, comment='是否系统设置'),
        sa.Column('requires_restart', sa.Boolean(), nullable=True, default=False, comment='是否需要重启'),
        
        # 修改记录
        sa.Column('last_modified_by', sa.Integer(), nullable=True, comment='最后修改者'),
        
        sa.ForeignKeyConstraint(['last_modified_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('setting_key')
    )


def downgrade():
    """删除音乐生成相关数据库表"""
    
    # 删除表（按依赖关系逆序）
    op.drop_table('music_generation_settings')
    op.drop_table('music_generation_usage_logs')
    op.drop_table('music_style_templates')
    op.drop_table('music_generation_batches')
    op.drop_table('generated_music_files')
    op.drop_table('music_scene_analyses')
    op.drop_table('music_generation_tasks')
    
    # 删除枚举类型
    try:
        sa.Enum(name='fademode').drop(op.get_bind())
    except:
        pass
    try:
        sa.Enum(name='musicscenetype').drop(op.get_bind())
    except:
        pass
    try:
        sa.Enum(name='musicgenerationstatus').drop(op.get_bind())
    except:
        pass 