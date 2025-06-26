"""Add system logs table

Revision ID: add_system_logs_table
Revises: 
Create Date: 2024-12-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_system_logs_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建系统日志表"""
    # 创建日志级别枚举
    log_level_enum = postgresql.ENUM(
        'debug', 'info', 'warning', 'error', 'critical',
        name='loglevel',
        create_type=False
    )
    log_level_enum.create(op.get_bind(), checkfirst=True)
    
    # 创建日志模块枚举
    log_module_enum = postgresql.ENUM(
        'system', 'tts', 'database', 'api', 'websocket', 'auth', 'file', 'synthesis', 'analysis',
        name='logmodule',
        create_type=False
    )
    log_module_enum.create(op.get_bind(), checkfirst=True)
    
    # 创建系统日志表
    op.create_table(
        'system_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level', log_level_enum, nullable=False),
        sa.Column('module', log_module_enum, nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('source_file', sa.String(255), nullable=True),
        sa.Column('source_line', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.String(50), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引以提高查询性能
    op.create_index('idx_system_logs_id', 'system_logs', ['id'])
    op.create_index('idx_system_logs_level', 'system_logs', ['level'])
    op.create_index('idx_system_logs_module', 'system_logs', ['module'])
    op.create_index('idx_system_logs_created_at', 'system_logs', ['created_at'])
    op.create_index('idx_system_logs_user_id', 'system_logs', ['user_id'])
    op.create_index('idx_system_logs_session_id', 'system_logs', ['session_id'])
    
    # 复合索引以提高复杂查询性能
    op.create_index('idx_log_level_time', 'system_logs', ['level', 'created_at'])
    op.create_index('idx_log_module_time', 'system_logs', ['module', 'created_at'])
    op.create_index('idx_log_user_time', 'system_logs', ['user_id', 'created_at'])


def downgrade():
    """删除系统日志表"""
    # 删除表
    op.drop_table('system_logs')
    
    # 删除枚举类型
    log_level_enum = postgresql.ENUM(name='loglevel')
    log_level_enum.drop(op.get_bind(), checkfirst=True)
    
    log_module_enum = postgresql.ENUM(name='logmodule')
    log_module_enum.drop(op.get_bind(), checkfirst=True)