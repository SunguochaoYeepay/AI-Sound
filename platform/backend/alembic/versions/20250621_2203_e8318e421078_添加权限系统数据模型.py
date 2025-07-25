"""添加权限系统数据模型

Revision ID: e8318e421078
Revises: be9b34de668d
Create Date: 2025-06-21 22:03:27.428658

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e8318e421078'
down_revision = 'be9b34de668d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('permissions',
    sa.Column('code', sa.String(length=100), nullable=False, comment='权限代码'),
    sa.Column('name', sa.String(length=100), nullable=False, comment='权限名称'),
    sa.Column('description', sa.Text(), nullable=True, comment='权限描述'),
    sa.Column('module', sa.String(length=50), nullable=False, comment='所属模块'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('roles',
    sa.Column('name', sa.String(length=50), nullable=False, comment='角色名称'),
    sa.Column('display_name', sa.String(length=100), nullable=False, comment='显示名称'),
    sa.Column('description', sa.Text(), nullable=True, comment='角色描述'),
    sa.Column('is_system', sa.Boolean(), nullable=True, comment='是否系统角色'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('username', sa.String(length=50), nullable=False, comment='用户名'),
    sa.Column('email', sa.String(length=100), nullable=False, comment='邮箱'),
    sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='密码哈希'),
    sa.Column('full_name', sa.String(length=100), nullable=True, comment='真实姓名'),
    sa.Column('avatar_url', sa.String(length=500), nullable=True, comment='头像URL'),
    sa.Column('status', sa.String(length=20), nullable=True, comment='用户状态'),
    sa.Column('is_verified', sa.Boolean(), nullable=True, comment='是否已验证邮箱'),
    sa.Column('is_superuser', sa.Boolean(), nullable=True, comment='是否超级管理员'),
    sa.Column('daily_quota', sa.Integer(), nullable=True, comment='每日TTS配额'),
    sa.Column('used_quota', sa.Integer(), nullable=True, comment='已使用配额'),
    sa.Column('quota_reset_date', sa.DateTime(), nullable=True, comment='配额重置日期'),
    sa.Column('last_login', sa.DateTime(), nullable=True, comment='最后登录时间'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('login_logs',
    sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
    sa.Column('username', sa.String(length=50), nullable=True, comment='用户名'),
    sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
    sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
    sa.Column('login_time', sa.DateTime(), nullable=True, comment='登录时间'),
    sa.Column('success', sa.Boolean(), nullable=False, comment='是否成功'),
    sa.Column('failure_reason', sa.String(length=200), nullable=True, comment='失败原因'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('role_permissions',
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('permission_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )
    op.create_table('user_roles',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'role_id')
    )
    op.create_table('user_sessions',
    sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
    sa.Column('token_id', sa.String(length=255), nullable=False, comment='Token ID'),
    sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
    sa.Column('user_agent', sa.Text(), nullable=True, comment='用户代理'),
    sa.Column('expires_at', sa.DateTime(), nullable=False, comment='过期时间'),
    sa.Column('revoked_at', sa.DateTime(), nullable=True, comment='撤销时间'),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='主键ID'),
    sa.Column('created_at', sa.DateTime(), nullable=True, comment='创建时间'),
    sa.Column('updated_at', sa.DateTime(), nullable=True, comment='更新时间'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_id')
    )
    op.alter_column('backup_configs', 'id',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.alter_column('backup_configs', 'config_key',
               existing_type=sa.VARCHAR(length=100),
               comment=None,
               existing_comment='配置键',
               existing_nullable=False)
    op.alter_column('backup_configs', 'config_value',
               existing_type=sa.TEXT(),
               comment=None,
               existing_comment='配置值',
               existing_nullable=True)
    op.alter_column('backup_configs', 'description',
               existing_type=sa.TEXT(),
               comment=None,
               existing_comment='配置描述',
               existing_nullable=True)
    op.alter_column('backup_configs', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='创建时间',
               existing_nullable=True)
    op.alter_column('backup_configs', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='更新时间',
               existing_nullable=True)
    op.create_index(op.f('ix_backup_configs_id'), 'backup_configs', ['id'], unique=False)
    op.drop_column('backup_configs', 'is_active')
    op.drop_column('backup_configs', 'updated_by')
    op.drop_column('backup_configs', 'config_type')
    op.drop_column('backup_configs', 'is_sensitive')
    op.drop_column('backup_configs', 'category')
    op.add_column('backup_schedules', sa.Column('encryption_enabled', sa.Boolean(), nullable=True))
    op.add_column('backup_schedules', sa.Column('storage_location', sa.String(length=50), nullable=True))
    op.add_column('backup_schedules', sa.Column('last_run_time', sa.DateTime(), nullable=True))
    op.add_column('backup_schedules', sa.Column('next_run_time', sa.DateTime(), nullable=True))
    op.alter_column('backup_schedules', 'id',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.alter_column('backup_schedules', 'schedule_name',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               comment=None,
               existing_comment='调度名称',
               existing_nullable=False)
    op.alter_column('backup_schedules', 'backup_type',
               existing_type=sa.VARCHAR(length=50),
               comment=None,
               existing_comment='备份类型',
               existing_nullable=False)
    op.alter_column('backup_schedules', 'cron_expression',
               existing_type=sa.VARCHAR(length=100),
               comment=None,
               existing_comment='Cron表达式',
               existing_nullable=False)
    op.alter_column('backup_schedules', 'is_enabled',
               existing_type=sa.BOOLEAN(),
               comment=None,
               existing_comment='是否启用',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'include_audio',
               existing_type=sa.BOOLEAN(),
               comment=None,
               existing_comment='是否包含音频',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'retention_days',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='保留天数',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'created_by',
               existing_type=sa.VARCHAR(length=100),
               comment=None,
               existing_comment='创建者',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='创建时间',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='更新时间',
               existing_nullable=True)
    op.create_index(op.f('ix_backup_schedules_id'), 'backup_schedules', ['id'], unique=False)
    op.drop_column('backup_schedules', 'success_count')
    op.drop_column('backup_schedules', 'failure_count')
    op.drop_column('backup_schedules', 'next_run')
    op.drop_column('backup_schedules', 'last_run')
    op.add_column('backup_stats', sa.Column('date', sa.DateTime(), nullable=False))
    op.alter_column('backup_stats', 'id',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.alter_column('backup_stats', 'total_backups',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='总备份数',
               existing_nullable=True)
    op.alter_column('backup_stats', 'successful_backups',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='成功备份数',
               existing_nullable=True)
    op.alter_column('backup_stats', 'failed_backups',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='失败备份数',
               existing_nullable=True)
    op.alter_column('backup_stats', 'total_storage_used',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               comment=None,
               existing_comment='总存储使用量(字节)',
               existing_nullable=True)
    op.alter_column('backup_stats', 'avg_backup_duration',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='平均备份时长(秒)',
               existing_nullable=True)
    op.alter_column('backup_stats', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='创建时间',
               existing_nullable=True)
    op.create_index(op.f('ix_backup_stats_id'), 'backup_stats', ['id'], unique=False)
    op.drop_column('backup_stats', 'incremental_backup_count')
    op.drop_column('backup_stats', 'updated_at')
    op.drop_column('backup_stats', 'stat_date')
    op.drop_column('backup_stats', 'full_backup_count')
    op.drop_column('backup_stats', 'manual_backup_count')
    op.alter_column('backup_tasks', 'id',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='主键ID',
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text("nextval('backup_tasks_id_seq'::regclass)"))
    op.alter_column('backup_tasks', 'task_name',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               comment=None,
               existing_comment='任务名称',
               existing_nullable=False)
    op.alter_column('backup_tasks', 'task_type',
               existing_type=sa.VARCHAR(length=50),
               comment=None,
               existing_comment='任务类型: full, incremental, manual',
               existing_nullable=False)
    op.alter_column('backup_tasks', 'status',
               existing_type=sa.VARCHAR(length=50),
               comment=None,
               existing_comment='任务状态',
               existing_nullable=False)
    op.alter_column('backup_tasks', 'start_time',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='开始时间',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'end_time',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='结束时间',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'duration_seconds',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='执行时长(秒)',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'file_path',
               existing_type=sa.TEXT(),
               type_=sa.String(length=500),
               comment=None,
               existing_comment='备份文件路径',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'file_size',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               comment=None,
               existing_comment='原始文件大小(字节)',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'compressed_size',
               existing_type=sa.BIGINT(),
               type_=sa.Integer(),
               comment=None,
               existing_comment='压缩后大小(字节)',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'progress_percentage',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='进度百分比',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'error_message',
               existing_type=sa.TEXT(),
               comment=None,
               existing_comment='错误信息',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'include_audio',
               existing_type=sa.BOOLEAN(),
               comment=None,
               existing_comment='是否包含音频文件',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'encryption_enabled',
               existing_type=sa.BOOLEAN(),
               comment=None,
               existing_comment='是否启用加密',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'storage_location',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=50),
               comment=None,
               existing_comment='存储位置',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'retention_days',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='保留天数',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'created_by',
               existing_type=sa.VARCHAR(length=100),
               comment=None,
               existing_comment='创建者',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'backup_metadata',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment=None,
               existing_comment='备份元数据',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='创建时间',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='更新时间',
               existing_nullable=True)
    op.create_index(op.f('ix_backup_tasks_id'), 'backup_tasks', ['id'], unique=False)
    op.drop_column('backup_tasks', 'backup_method')
    op.add_column('restore_tasks', sa.Column('restore_metadata', sa.JSON(), nullable=True))
    op.alter_column('restore_tasks', 'id',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.alter_column('restore_tasks', 'backup_id',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='关联备份ID',
               existing_nullable=False)
    op.alter_column('restore_tasks', 'task_name',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               comment=None,
               existing_comment='恢复任务名称',
               existing_nullable=False)
    op.alter_column('restore_tasks', 'restore_type',
               existing_type=sa.VARCHAR(length=50),
               nullable=False,
               comment=None,
               existing_comment='恢复类型: full, partial, point_in_time')
    op.alter_column('restore_tasks', 'target_database',
               existing_type=sa.VARCHAR(length=100),
               nullable=False,
               comment=None,
               existing_comment='目标数据库')
    op.alter_column('restore_tasks', 'status',
               existing_type=sa.VARCHAR(length=50),
               comment=None,
               existing_comment='恢复状态',
               existing_nullable=False)
    op.alter_column('restore_tasks', 'start_time',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='开始时间',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'end_time',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='结束时间',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'duration_seconds',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='恢复时长(秒)',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'progress_percentage',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='恢复进度',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'error_message',
               existing_type=sa.TEXT(),
               comment=None,
               existing_comment='错误信息',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'include_audio',
               existing_type=sa.BOOLEAN(),
               comment=None,
               existing_comment='是否恢复音频文件',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'restore_point',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='恢复到的时间点',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'created_by',
               existing_type=sa.VARCHAR(length=100),
               comment=None,
               existing_comment='创建者',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='创建时间',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='更新时间',
               existing_nullable=True)
    op.create_index(op.f('ix_restore_tasks_id'), 'restore_tasks', ['id'], unique=False)
    op.drop_constraint('restore_tasks_backup_id_fkey', 'restore_tasks', type_='foreignkey')
    op.drop_column('restore_tasks', 'validation_result')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('restore_tasks', sa.Column('validation_result', sa.TEXT(), autoincrement=False, nullable=True, comment='验证结果'))
    op.create_foreign_key('restore_tasks_backup_id_fkey', 'restore_tasks', 'backup_tasks', ['backup_id'], ['id'])
    op.drop_index(op.f('ix_restore_tasks_id'), table_name='restore_tasks')
    op.alter_column('restore_tasks', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='更新时间',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='创建时间',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'created_by',
               existing_type=sa.VARCHAR(length=100),
               comment='创建者',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'restore_point',
               existing_type=postgresql.TIMESTAMP(),
               comment='恢复到的时间点',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'include_audio',
               existing_type=sa.BOOLEAN(),
               comment='是否恢复音频文件',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'error_message',
               existing_type=sa.TEXT(),
               comment='错误信息',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'progress_percentage',
               existing_type=sa.INTEGER(),
               comment='恢复进度',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'duration_seconds',
               existing_type=sa.INTEGER(),
               comment='恢复时长(秒)',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'end_time',
               existing_type=postgresql.TIMESTAMP(),
               comment='结束时间',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'start_time',
               existing_type=postgresql.TIMESTAMP(),
               comment='开始时间',
               existing_nullable=True)
    op.alter_column('restore_tasks', 'status',
               existing_type=sa.VARCHAR(length=50),
               comment='恢复状态',
               existing_nullable=False)
    op.alter_column('restore_tasks', 'target_database',
               existing_type=sa.VARCHAR(length=100),
               nullable=True,
               comment='目标数据库')
    op.alter_column('restore_tasks', 'restore_type',
               existing_type=sa.VARCHAR(length=50),
               nullable=True,
               comment='恢复类型: full, partial, point_in_time')
    op.alter_column('restore_tasks', 'task_name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               comment='恢复任务名称',
               existing_nullable=False)
    op.alter_column('restore_tasks', 'backup_id',
               existing_type=sa.INTEGER(),
               comment='关联备份ID',
               existing_nullable=False)
    op.alter_column('restore_tasks', 'id',
               existing_type=sa.INTEGER(),
               comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.drop_column('restore_tasks', 'restore_metadata')
    op.add_column('backup_tasks', sa.Column('backup_method', sa.VARCHAR(length=50), autoincrement=False, nullable=True, comment='备份方法: pg_dump, pg_basebackup'))
    op.drop_index(op.f('ix_backup_tasks_id'), table_name='backup_tasks')
    op.alter_column('backup_tasks', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='更新时间',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='创建时间',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'backup_metadata',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment='备份元数据',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'created_by',
               existing_type=sa.VARCHAR(length=100),
               comment='创建者',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'retention_days',
               existing_type=sa.INTEGER(),
               comment='保留天数',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'storage_location',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=100),
               comment='存储位置',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'encryption_enabled',
               existing_type=sa.BOOLEAN(),
               comment='是否启用加密',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'include_audio',
               existing_type=sa.BOOLEAN(),
               comment='是否包含音频文件',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'error_message',
               existing_type=sa.TEXT(),
               comment='错误信息',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'progress_percentage',
               existing_type=sa.INTEGER(),
               comment='进度百分比',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'compressed_size',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               comment='压缩后大小(字节)',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'file_size',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               comment='原始文件大小(字节)',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'file_path',
               existing_type=sa.String(length=500),
               type_=sa.TEXT(),
               comment='备份文件路径',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'duration_seconds',
               existing_type=sa.INTEGER(),
               comment='执行时长(秒)',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'end_time',
               existing_type=postgresql.TIMESTAMP(),
               comment='结束时间',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'start_time',
               existing_type=postgresql.TIMESTAMP(),
               comment='开始时间',
               existing_nullable=True)
    op.alter_column('backup_tasks', 'status',
               existing_type=sa.VARCHAR(length=50),
               comment='任务状态',
               existing_nullable=False)
    op.alter_column('backup_tasks', 'task_type',
               existing_type=sa.VARCHAR(length=50),
               comment='任务类型: full, incremental, manual',
               existing_nullable=False)
    op.alter_column('backup_tasks', 'task_name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               comment='任务名称',
               existing_nullable=False)
    op.alter_column('backup_tasks', 'id',
               existing_type=sa.INTEGER(),
               comment='主键ID',
               existing_nullable=False,
               autoincrement=True,
               existing_server_default=sa.text("nextval('backup_tasks_id_seq'::regclass)"))
    op.add_column('backup_stats', sa.Column('manual_backup_count', sa.INTEGER(), autoincrement=False, nullable=True, comment='手动备份数'))
    op.add_column('backup_stats', sa.Column('full_backup_count', sa.INTEGER(), autoincrement=False, nullable=True, comment='全量备份数'))
    op.add_column('backup_stats', sa.Column('stat_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True, comment='统计日期'))
    op.add_column('backup_stats', sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True, comment='更新时间'))
    op.add_column('backup_stats', sa.Column('incremental_backup_count', sa.INTEGER(), autoincrement=False, nullable=True, comment='增量备份数'))
    op.drop_index(op.f('ix_backup_stats_id'), table_name='backup_stats')
    op.alter_column('backup_stats', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='创建时间',
               existing_nullable=True)
    op.alter_column('backup_stats', 'avg_backup_duration',
               existing_type=sa.INTEGER(),
               comment='平均备份时长(秒)',
               existing_nullable=True)
    op.alter_column('backup_stats', 'total_storage_used',
               existing_type=sa.Integer(),
               type_=sa.BIGINT(),
               comment='总存储使用量(字节)',
               existing_nullable=True)
    op.alter_column('backup_stats', 'failed_backups',
               existing_type=sa.INTEGER(),
               comment='失败备份数',
               existing_nullable=True)
    op.alter_column('backup_stats', 'successful_backups',
               existing_type=sa.INTEGER(),
               comment='成功备份数',
               existing_nullable=True)
    op.alter_column('backup_stats', 'total_backups',
               existing_type=sa.INTEGER(),
               comment='总备份数',
               existing_nullable=True)
    op.alter_column('backup_stats', 'id',
               existing_type=sa.INTEGER(),
               comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.drop_column('backup_stats', 'date')
    op.add_column('backup_schedules', sa.Column('last_run', postgresql.TIMESTAMP(), autoincrement=False, nullable=True, comment='上次运行时间'))
    op.add_column('backup_schedules', sa.Column('next_run', postgresql.TIMESTAMP(), autoincrement=False, nullable=True, comment='下次运行时间'))
    op.add_column('backup_schedules', sa.Column('failure_count', sa.INTEGER(), autoincrement=False, nullable=True, comment='失败次数'))
    op.add_column('backup_schedules', sa.Column('success_count', sa.INTEGER(), autoincrement=False, nullable=True, comment='成功次数'))
    op.drop_index(op.f('ix_backup_schedules_id'), table_name='backup_schedules')
    op.alter_column('backup_schedules', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='更新时间',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='创建时间',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'created_by',
               existing_type=sa.VARCHAR(length=100),
               comment='创建者',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'retention_days',
               existing_type=sa.INTEGER(),
               comment='保留天数',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'include_audio',
               existing_type=sa.BOOLEAN(),
               comment='是否包含音频',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'is_enabled',
               existing_type=sa.BOOLEAN(),
               comment='是否启用',
               existing_nullable=True)
    op.alter_column('backup_schedules', 'cron_expression',
               existing_type=sa.VARCHAR(length=100),
               comment='Cron表达式',
               existing_nullable=False)
    op.alter_column('backup_schedules', 'backup_type',
               existing_type=sa.VARCHAR(length=50),
               comment='备份类型',
               existing_nullable=False)
    op.alter_column('backup_schedules', 'schedule_name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               comment='调度名称',
               existing_nullable=False)
    op.alter_column('backup_schedules', 'id',
               existing_type=sa.INTEGER(),
               comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.drop_column('backup_schedules', 'next_run_time')
    op.drop_column('backup_schedules', 'last_run_time')
    op.drop_column('backup_schedules', 'storage_location')
    op.drop_column('backup_schedules', 'encryption_enabled')
    op.add_column('backup_configs', sa.Column('category', sa.VARCHAR(length=50), autoincrement=False, nullable=True, comment='配置分类: schedule, storage, security, notification'))
    op.add_column('backup_configs', sa.Column('is_sensitive', sa.BOOLEAN(), autoincrement=False, nullable=True, comment='是否敏感信息'))
    op.add_column('backup_configs', sa.Column('config_type', sa.VARCHAR(length=50), autoincrement=False, nullable=True, comment='配置类型: string, integer, boolean, json'))
    op.add_column('backup_configs', sa.Column('updated_by', sa.VARCHAR(length=100), autoincrement=False, nullable=True, comment='更新者'))
    op.add_column('backup_configs', sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True, comment='是否生效'))
    op.drop_index(op.f('ix_backup_configs_id'), table_name='backup_configs')
    op.alter_column('backup_configs', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='更新时间',
               existing_nullable=True)
    op.alter_column('backup_configs', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='创建时间',
               existing_nullable=True)
    op.alter_column('backup_configs', 'description',
               existing_type=sa.TEXT(),
               comment='配置描述',
               existing_nullable=True)
    op.alter_column('backup_configs', 'config_value',
               existing_type=sa.TEXT(),
               comment='配置值',
               existing_nullable=True)
    op.alter_column('backup_configs', 'config_key',
               existing_type=sa.VARCHAR(length=100),
               comment='配置键',
               existing_nullable=False)
    op.alter_column('backup_configs', 'id',
               existing_type=sa.INTEGER(),
               comment='主键ID',
               existing_nullable=False,
               autoincrement=True)
    op.drop_table('user_sessions')
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('login_logs')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('permissions')
    # ### end Alembic commands ### 