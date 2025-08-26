# 手动MySQL数据库设置指南

## 方法1：使用phpMyAdmin（推荐）

### 步骤1：启动XAMPP
1. 打开XAMPP控制面板
2. 启动Apache和MySQL服务
3. 点击MySQL行的"Admin"按钮，打开phpMyAdmin

### 步骤2：创建数据库
1. 在phpMyAdmin中点击"新建"
2. 数据库名称：`ai_sound`
3. 字符集：`utf8mb4_unicode_ci`
4. 点击"创建"

### 步骤3：创建用户
1. 点击"用户账户"标签
2. 点击"添加用户账户"
3. 用户名：`ai_sound_user`
4. 主机名：`localhost`
5. 密码：`ai_sound_password`
6. 勾选"创建数据库时授予所有权限"
7. 点击"执行"

## 方法2：使用MySQL Workbench

### 步骤1：连接MySQL
1. 打开MySQL Workbench
2. 创建新连接：
   - Hostname: `localhost`
   - Port: `3306`
   - Username: `root`
   - Password: (你的root密码)

### 步骤2：执行SQL脚本
```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_sound 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER IF NOT EXISTS 'ai_sound_user'@'localhost' 
IDENTIFIED BY 'ai_sound_password';

-- 授权
GRANT ALL PRIVILEGES ON ai_sound.* TO 'ai_sound_user'@'localhost';
FLUSH PRIVILEGES;
```

## 验证设置

### 测试连接
```bash
# 使用XAMPP MySQL命令行工具
C:\xampp\mysql\bin\mysql.exe -u ai_sound_user -p ai_sound

# 或者使用MySQL Workbench连接测试
```

### 检查数据库
```sql
-- 查看数据库
SHOW DATABASES;

-- 查看用户
SELECT User, Host FROM mysql.user WHERE User = 'ai_sound_user';

-- 查看权限
SHOW GRANTS FOR 'ai_sound_user'@'localhost';
```

## 常见问题

### 1. 连接被拒绝
- 检查MySQL服务是否启动
- 检查端口3306是否被占用
- 检查防火墙设置

### 2. 权限错误
- 确保使用root用户创建数据库和用户
- 检查用户权限设置

### 3. 字符集问题
- 确保使用utf8mb4字符集
- 检查数据库和表的字符集设置
