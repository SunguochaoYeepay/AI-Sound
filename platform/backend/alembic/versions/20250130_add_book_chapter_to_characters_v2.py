"""add book chapter to characters v2

Revision ID: 20250130_add_book_chapter_v2
Revises: d4b17c87ccee
Create Date: 2025-01-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250130_add_book_chapter_v2'
down_revision = 'd4b17c87ccee'
branch_labels = None
depends_on = None

def upgrade():
    # 检查characters表是否存在book_id和chapter_id字段
    # 如果不存在则添加
    try:
        # 添加book_id和chapter_id字段
        op.add_column('characters', sa.Column('book_id', sa.Integer(), nullable=True))
        op.add_column('characters', sa.Column('chapter_id', sa.Integer(), nullable=True))
        
        # 添加外键约束（如果表存在的话）
        try:
            op.create_foreign_key(
                'fk_characters_book_id',
                'characters', 'books',
                ['book_id'], ['id'],
                ondelete='SET NULL'
            )
        except:
            pass  # 如果books表不存在，跳过外键约束
            
        try:
            op.create_foreign_key(
                'fk_characters_chapter_id',
                'characters', 'chapters',
                ['chapter_id'], ['id'],
                ondelete='SET NULL'
            )
        except:
            pass  # 如果chapters表不存在，跳过外键约束
            
    except Exception as e:
        # 如果字段已存在，跳过
        print(f"字段可能已存在: {e}")

def downgrade():
    # 删除外键约束
    try:
        op.drop_constraint('fk_characters_chapter_id', 'characters', type_='foreignkey')
    except:
        pass
        
    try:
        op.drop_constraint('fk_characters_book_id', 'characters', type_='foreignkey')
    except:
        pass
    
    # 删除字段
    try:
        op.drop_column('characters', 'chapter_id')
        op.drop_column('characters', 'book_id')
    except:
        pass 