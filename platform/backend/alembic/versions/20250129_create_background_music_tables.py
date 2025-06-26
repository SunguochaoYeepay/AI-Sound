"""创建背景音乐库表

Revision ID: 20250129_create_background_music_tables
Revises: 
Create Date: 2025-01-29 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250129_create_background_music_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建背景音乐相关表"""
    
    # 创建音乐分类表
    op.create_table('music_categories',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('name', sa.String(length=100), nullable=False, comment='分类名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='分类描述'),
        sa.Column('icon', sa.String(length=50), nullable=True, comment='分类图标'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True, comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_music_categories_id'), 'music_categories', ['id'], unique=False)
    
    # 创建背景音乐表
    op.create_table('background_music',
        sa.Column('id', sa.Integer(), nullable=False, comment='主键ID'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='音乐名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='音乐描述'),
        sa.Column('filename', sa.String(length=255), nullable=False, comment='文件名'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='文件路径'),
        sa.Column('file_size', sa.Integer(), nullable=True, comment='文件大小(字节)'),
        sa.Column('duration', sa.Float(), nullable=True, comment='时长(秒)'),
        sa.Column('category_id', sa.Integer(), nullable=True, comment='分类ID'),
        sa.Column('emotion_tags', sa.JSON(), nullable=True, comment='情感标签JSON数组'),
        sa.Column('style_tags', sa.JSON(), nullable=True, comment='风格标签JSON数组'),
        sa.Column('quality_rating', sa.Float(), nullable=True, default=3.0, comment='质量评分(1-5)'),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0, comment='使用次数'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, comment='最后使用时间'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True, comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['category_id'], ['music_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_background_music_id'), 'background_music', ['id'], unique=False)
    
    # 插入默认分类数据
    op.execute("""
        INSERT INTO music_categories (name, description, icon, is_active, created_at, updated_at)
        VALUES 
        ('环境音乐', '自然环境、氛围音效', 'nature', 1, datetime('now'), datetime('now')),
        ('古典音乐', '古典乐曲、管弦乐', 'classical', 1, datetime('now'), datetime('now')),
        ('电子音乐', '电子合成音乐', 'electronic', 1, datetime('now'), datetime('now')),
        ('电影配乐', '电影原声、影视音乐', 'movie', 1, datetime('now'), datetime('now')),
        ('爵士音乐', '爵士乐、蓝调音乐', 'jazz', 1, datetime('now'), datetime('now'))
    """)


def downgrade():
    """删除背景音乐相关表"""
    op.drop_index(op.f('ix_background_music_id'), table_name='background_music')
    op.drop_table('background_music')
    op.drop_index(op.f('ix_music_categories_id'), table_name='music_categories')
    op.drop_table('music_categories')