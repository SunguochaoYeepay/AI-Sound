"""Add image generation tables

Revision ID: add_image_generation_20250131
Revises: 20250127_add_name_to_music_generation_tasks
Create Date: 2025-01-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_image_generation_20250131'
down_revision = '20250127_add_name_to_music_generation_tasks'
branch_labels = None
depends_on = None


def upgrade():
    """添加图片生成相关表"""
    # 创建图片生成任务表
    op.create_table(
        'image_generation_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('analysis_result_id', sa.Integer(), nullable=True),
        sa.Column('segment_index', sa.Integer(), nullable=False, comment='段落索引'),
        sa.Column('segment_text', sa.Text(), nullable=False, comment='段落原文'),
        sa.Column('segment_type', sa.String(length=50), nullable=True, comment='段落类型: dialogue, narrative, description'),
        sa.Column('scene_description', sa.Text(), nullable=True, comment='场景描述'),
        sa.Column('character_info', sa.JSON(), nullable=True, comment='角色信息'),
        sa.Column('emotional_tone', sa.String(length=100), nullable=True, comment='情感色调'),
        sa.Column('style_keywords', sa.JSON(), nullable=True, comment='风格关键词'),
        sa.Column('comfyui_workflow', sa.JSON(), nullable=True, comment='ComfyUI工作流配置'),
        sa.Column('generated_prompt', sa.Text(), nullable=True, comment='最终生成的提示词'),
        sa.Column('negative_prompt', sa.Text(), nullable=True, comment='负面提示词'),
        sa.Column('image_width', sa.Integer(), nullable=True, comment='图片宽度'),
        sa.Column('image_height', sa.Integer(), nullable=True, comment='图片高度'),
        sa.Column('generation_model', sa.String(length=100), nullable=True, comment='生成模型'),
        sa.Column('generation_params', sa.JSON(), nullable=True, comment='生成参数'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='pending, processing, completed, failed'),
        sa.Column('progress', sa.Integer(), nullable=True, comment='进度 0-100'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
        sa.Column('generated_image_url', sa.String(length=500), nullable=True, comment='生成的图片URL'),
        sa.Column('generated_image_path', sa.String(length=500), nullable=True, comment='生成的图片本地路径'),
        sa.Column('generation_seed', sa.Integer(), nullable=True, comment='生成种子'),
        sa.Column('generation_time', sa.Integer(), nullable=True, comment='生成耗时(秒)'),
        sa.Column('quality_score', sa.Integer(), nullable=True, comment='质量评分 0-100'),
        sa.Column('user_rating', sa.Integer(), nullable=True, comment='用户评分 1-5'),
        sa.Column('is_approved', sa.Boolean(), nullable=True, comment='是否通过审核'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='开始生成时间'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='完成时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_result_id'], ['analysis_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chapter_id'], ['book_chapters.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_image_generation_chapter_id', 'image_generation_tasks', ['chapter_id'])
    op.create_index('idx_image_generation_status', 'image_generation_tasks', ['status'])
    op.create_index('idx_image_generation_chapter_segment', 'image_generation_tasks', ['chapter_id', 'segment_index'])
    op.create_index('idx_image_generation_analysis_result', 'image_generation_tasks', ['analysis_result_id'])
    op.create_index(op.f('ix_image_generation_tasks_id'), 'image_generation_tasks', ['id'])

    # 创建图片生成预设表
    op.create_table(
        'image_generation_presets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='预设名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='预设描述'),
        sa.Column('category', sa.String(length=50), nullable=True, comment='预设分类: general, character, scene, emotion'),
        sa.Column('default_workflow', sa.JSON(), nullable=True, comment='默认ComfyUI工作流'),
        sa.Column('prompt_template', sa.Text(), nullable=True, comment='提示词模板'),
        sa.Column('negative_prompt_template', sa.Text(), nullable=True, comment='负面提示词模板'),
        sa.Column('style_keywords', sa.JSON(), nullable=True, comment='风格关键词'),
        sa.Column('default_params', sa.JSON(), nullable=True, comment='默认生成参数'),
        sa.Column('recommended_models', sa.JSON(), nullable=True, comment='推荐模型列表'),
        sa.Column('is_public', sa.Boolean(), nullable=True, comment='是否公开'),
        sa.Column('usage_count', sa.Integer(), nullable=True, comment='使用次数'),
        sa.Column('success_rate', sa.Integer(), nullable=True, comment='成功率百分比'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('idx_image_presets_category', 'image_generation_presets', ['category'])
    op.create_index('idx_image_presets_public', 'image_generation_presets', ['is_public'])
    op.create_index(op.f('ix_image_generation_presets_id'), 'image_generation_presets', ['id'])

    # 设置默认值
    op.execute("""
        UPDATE image_generation_tasks 
        SET segment_type = 'narrative' 
        WHERE segment_type IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_tasks 
        SET image_width = 1024, image_height = 1024 
        WHERE image_width IS NULL OR image_height IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_tasks 
        SET generation_model = 'SD1.5' 
        WHERE generation_model IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_tasks 
        SET status = 'pending' 
        WHERE status IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_tasks 
        SET progress = 0 
        WHERE progress IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_tasks 
        SET is_approved = false 
        WHERE is_approved IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_presets 
        SET category = 'general' 
        WHERE category IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_presets 
        SET is_public = true 
        WHERE is_public IS NULL
    """)
    
    op.execute("""
        UPDATE image_generation_presets 
        SET usage_count = 0, success_rate = 0 
        WHERE usage_count IS NULL OR success_rate IS NULL
    """)


def downgrade():
    """删除图片生成相关表"""
    # 删除索引
    op.drop_index(op.f('ix_image_generation_presets_id'), table_name='image_generation_presets')
    op.drop_index('idx_image_presets_public', table_name='image_generation_presets')
    op.drop_index('idx_image_presets_category', table_name='image_generation_presets')
    
    op.drop_index(op.f('ix_image_generation_tasks_id'), table_name='image_generation_tasks')
    op.drop_index('idx_image_generation_analysis_result', table_name='image_generation_tasks')
    op.drop_index('idx_image_generation_chapter_segment', table_name='image_generation_tasks')
    op.drop_index('idx_image_generation_status', table_name='image_generation_tasks')
    op.drop_index('idx_image_generation_chapter_id', table_name='image_generation_tasks')
    
    # 删除表
    op.drop_table('image_generation_presets')
    op.drop_table('image_generation_tasks') 