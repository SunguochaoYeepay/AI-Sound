# 🚀 AI-Sound 本地部署指南 (MySQL版本)

## 🎯 为什么选择本地部署？

### Docker部署的问题
- **资源消耗大**: 多个AI服务容器同时运行内存压力大
- **Windows兼容性**: Docker Desktop在Windows上性能问题
- **网络配置复杂**: 容器间通信配置繁琐
- **调试困难**: 容器内调试不如本地直接调试

### 本地部署优势
- **资源利用率高**: 直接使用系统资源，无容器开销
- **调试方便**: 代码修改即时生效，断点调试
- **启动速度快**: 无需容器启动时间
- **配置简单**: 环境变量和路径配置更直观

## 📋 环境要求

### 必需软件
- **Python 3.9-3.11** (推荐3.10)
- **MySQL 8.0+** (推荐8.0.33)
- **Redis 7.0+** (可选，用于缓存)

### 可选软件
- **XAMPP/WAMP**: 集成MySQL和Redis环境
- **MySQL Workbench**: 数据库管理工具

## 🛠️ 安装步骤

### 第一步：安装MySQL

#### 方式1：独立安装MySQL
1. 下载MySQL 8.0: https://dev.mysql.com/downloads/mysql/
2. 安装时设置root密码
3. 启动MySQL服务

#### 方式2：使用XAMPP (推荐)
1. 下载XAMPP: https://www.apachefriends.org/
2. 安装后启动MySQL服务
3. 默认端口3306，root密码为空

### 第二步：安装Redis (可选)

#### 方式1：独立安装Redis
1. 下载Redis for Windows: https://github.com/tporadowski/redis/releases
2. 安装并启动Redis服务

#### 方式2：使用Docker运行Redis
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 第三步：初始化数据库

```bash
# 运行数据库初始化脚本
scripts\setup-mysql.bat
```

### 第四步：启动后端服务

```bash
# 运行本地启动脚本
scripts\local-start.bat
```

## 🔧 配置说明

### 环境变量配置

复制环境配置文件：
```bash
cd platform/backend
copy env.mysql.example .env
```

主要配置项：
```env
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=ai_sound_user
MYSQL_PASSWORD=ai_sound_password
MYSQL_DATABASE=ai_sound

# AI服务配置
MEGATTS3_URL=http://localhost:7929
TANGOFLUX_URL=http://localhost:7930
SONGGENERATION_URL=http://localhost:7862
```

### 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端API | 8000 | FastAPI后端服务 |
| MySQL | 3306 | 数据库服务 |
| Redis | 6379 | 缓存服务 |
| MegaTTS3 | 7929 | 语音合成服务 |
| TangoFlux | 7930 | 环境音生成服务 |
| SongGeneration | 7862 | 背景音乐生成服务 |

## 🚀 启动流程

### 完整启动流程

1. **启动MySQL服务**
   ```bash
   net start mysql
   # 或使用XAMPP控制面板启动
   ```

2. **启动Redis服务** (可选)
   ```bash
   net start redis
   # 或使用Docker: docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **初始化数据库**
   ```bash
   scripts\setup-mysql.bat
   ```

4. **启动后端服务**
   ```bash
   scripts\local-start.bat
   ```

5. **启动前端服务** (可选)
   ```bash
   cd platform/frontend
   npm install
   npm run dev
   ```

### 验证服务状态

访问以下地址验证服务：
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 🔍 故障排除

### 常见问题

#### 1. MySQL连接失败
**症状**: `Can't connect to MySQL server`
**解决**:
```bash
# 检查MySQL服务状态
net start mysql

# 检查端口是否被占用
netstat -an | findstr :3306

# 检查防火墙设置
```

#### 2. Python依赖安装失败
**症状**: `pip install` 失败
**解决**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 清理缓存
pip cache purge

# 重新安装
pip install -r requirements-mysql.txt --force-reinstall
```

#### 3. 数据库表创建失败
**症状**: `Table creation failed`
**解决**:
```bash
# 检查数据库连接
mysql -u ai_sound_user -p ai_sound

# 检查用户权限
SHOW GRANTS FOR 'ai_sound_user'@'localhost';
```

#### 4. 端口被占用
**症状**: `Address already in use`
**解决**:
```bash
# 查看端口占用
netstat -ano | findstr :8000

# 结束占用进程
taskkill /PID <进程ID> /F
```

## 📊 性能优化

### MySQL优化
```sql
-- 设置MySQL优化参数
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB
SET GLOBAL max_connections = 200;
SET GLOBAL query_cache_size = 67108864; -- 64MB
```

### Python优化
```bash
# 使用生产模式启动
set DEBUG=false
set ECHO_SQL=false

# 使用uvicorn生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔄 数据迁移

### 从PostgreSQL迁移到MySQL

1. **导出PostgreSQL数据**
   ```bash
   pg_dump -U ai_sound_user -h localhost ai_sound > backup.sql
   ```

2. **转换数据格式**
   ```bash
   # 使用工具转换SQL语法
   # 注意：PostgreSQL和MySQL语法有差异
   ```

3. **导入MySQL数据**
   ```bash
   mysql -u ai_sound_user -p ai_sound < backup_converted.sql
   ```

## 📝 开发建议

### 日常开发流程

1. **启动开发环境**
   ```bash
   scripts\local-start.bat
   ```

2. **修改代码**
   - 后端代码修改后自动重载
   - 前端代码需要重新构建

3. **调试和测试**
   - 使用断点调试
   - 查看详细日志
   - 使用API文档测试

### 代码热重载

本地部署支持代码热重载：
- 修改Python代码后自动重启
- 无需手动重启服务
- 提高开发效率

## 🎉 总结

本地部署的优势：
- ✅ **资源利用率高**: 无容器开销
- ✅ **调试方便**: 直接调试，热重载
- ✅ **配置简单**: 环境变量配置
- ✅ **启动快速**: 无需容器启动时间
- ✅ **MySQL稳定**: Windows兼容性好

推荐使用本地部署 + MySQL的组合，可以显著提升开发效率和系统稳定性。
