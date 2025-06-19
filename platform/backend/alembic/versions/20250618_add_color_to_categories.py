"""add color to environment sound categories

Revision ID: 20250618_add_color
Revises: 20250618_make_project_optional
Create Date: 2025-06-18 13:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250618_add_color'
down_revision = '20250618_make_project_optional'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add color column to environment_sound_categories table
    op.add_column('environment_sound_categories', 
                  sa.Column('color', sa.String(7), nullable=True, server_default='#1890ff'))
    
    # Update existing records with default colors
    op.execute("""
        UPDATE environment_sound_categories 
        SET color = CASE 
            WHEN name = '自然音效' THEN '#52c41a'
            WHEN name = '城市环境' THEN '#1890ff'
            WHEN name = '室内环境' THEN '#fa8c16'
            WHEN name = '交通工具' THEN '#722ed1'
            WHEN name = '动物声音' THEN '#eb2f96'
            WHEN name = '人声效果' THEN '#f5222d'
            WHEN name = '机械设备' THEN '#faad14'
            WHEN name = '乐器声音' THEN '#13c2c2'
            WHEN name = '电子音效' THEN '#2f54eb'
            ELSE '#1890ff'
        END
    """)


def downgrade() -> None:
    # Remove color column from environment_sound_categories table
    op.drop_column('environment_sound_categories', 'color') 