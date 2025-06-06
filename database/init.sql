-- AI-Sound PostgreSQL初始化脚本
-- 该文件在PostgreSQL容器首次启动时自动执行

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 设置时区
SET TIME ZONE 'Asia/Shanghai';

-- 数据库已由POSTGRES_DB环境变量创建，这里只需要初始化配置