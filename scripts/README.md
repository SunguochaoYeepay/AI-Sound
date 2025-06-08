# 🚀 AI-Sound 自动化脚本工具集

本目录包含 AI-Sound 项目的各种自动化脚本，提供完整的开发、部署和维护工具链。

## 📁 脚本概览

### 🔨 部署脚本
- **`frontend-deploy.bat`** - Windows前端自动构建部署脚本
- **`frontend-deploy.sh`** - Linux/macOS前端自动构建部署脚本
- **`deploy.sh`** - 完整项目一键部署脚本（Linux/macOS）
- **`deploy.bat`** - 完整项目一键部署脚本（Windows）

### 🔍 监控脚本
- **`megatts3_health.sh`** - MegaTTS3服务健康检查脚本

### 📊 分析工具
- **`analysis/`** - 语音分析工具目录
  - `analyze_voice_features.py` - 语音特征分析
  - `check_npy_shape.py` - NPY文件检查
  - `check_model_load.py` - 模型加载测试

## 🎯 前端部署脚本使用指南

### Windows用户

#### 基本使用
```batch
# 生产模式部署（默认）
.\scripts\frontend-deploy.bat

# 开发模式部署
.\scripts\frontend-deploy.bat dev

# 明确指定生产模式
.\scripts\frontend-deploy.bat prod
```

#### 脚本功能
1. **🏗️ 自动构建** - 执行 `npm run build` 构建前端代码
2. **🧹 清理目录** - 清空 `nginx-dist` 目录
3. **📂 文件拷贝** - 将构建结果复制到nginx目录
4. **🔄 容器重启** - 重启nginx容器加载新代码
5. **📊 状态检查** - 显示容器运行状态

### Linux/macOS用户

#### 基本使用
```bash
# 生产模式部署（默认）
./scripts/frontend-deploy.sh

# 开发模式部署  
./scripts/frontend-deploy.sh dev

# 明确指定生产模式
./scripts/frontend-deploy.sh prod
```

#### 脚本功能
- **智能依赖检查** - 自动检测npm、docker-compose是否可用
- **自动安装依赖** - 如果node_modules不存在，自动执行npm install
- **彩色输出** - 友好的终端界面，带状态提示
- **错误处理** - 完善的错误处理和提示信息

## 🛠️ 完整部署脚本

### 一键部署（推荐）

#### Linux/macOS
```bash
# 生产部署
./scripts/deploy.sh

# 开发部署
./scripts/deploy.sh dev

# 清理环境
./scripts/deploy.sh clean
```

#### Windows
```batch
# 生产部署
.\scripts\deploy.bat

# 开发部署
.\scripts\deploy.bat dev

# 清理环境
.\scripts\deploy.bat clean
```

### 功能特性
- **环境检查** - 检查Docker、Docker Compose、Node.js等依赖
- **自动构建** - 前端代码构建和优化
- **容器管理** - Docker容器的启动、停止、重建
- **健康检查** - 服务启动后的健康状态验证
- **日志输出** - 详细的部署过程日志

## 🔍 监控工具

### MegaTTS3健康检查
```bash
# 执行健康检查
./scripts/megatts3_health.sh

# 检查内容：
# - GPU状态和显存使用
# - 系统资源（CPU、内存、磁盘）
# - 网络连接状态
# - MegaTTS3服务响应
```

## 📊 分析工具使用

### 语音特征分析
```bash
# 分析音频文件特征
python scripts/analysis/analyze_voice_features.py [audio_file]

# 批量分析目录下的音频文件
python scripts/analysis/analyze_voice_features.py [directory]
```

### NPY文件检查
```bash
# 检查NPY文件的形状和内容
python scripts/analysis/check_npy_shape.py [npy_file]
```

### 模型加载测试
```bash
# 测试模型是否能正常加载
python scripts/analysis/check_model_load.py [model_path]
```

## 🚨 故障排查

### 常见问题

#### 1. 前端构建失败
```bash
# 清理node_modules重新安装
cd platform/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### 2. Docker容器无法启动
```bash
# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs nginx
docker-compose logs backend

# 重启所有服务
docker-compose restart
```

#### 3. 文件拷贝权限错误
```bash
# Linux/macOS - 检查文件权限
ls -la nginx-dist/
chmod -R 755 nginx-dist/

# Windows - 以管理员身份运行脚本
```

#### 4. 端口占用问题
```bash
# 检查端口占用
netstat -tulpn | grep :3001
netstat -tulpn | grep :8000

# Windows
netstat -ano | findstr :3001
```

### 诊断命令

```bash
# 检查Docker状态
docker --version
docker-compose --version
docker ps -a

# 检查磁盘空间
df -h

# 检查系统资源
htop  # Linux
top   # macOS

# Windows系统信息
systeminfo
```

## 📝 开发建议

### 修改脚本后的测试流程
1. **备份原脚本** - 修改前备份工作版本
2. **小步测试** - 每次修改后立即测试
3. **错误处理** - 添加详细的错误提示
4. **兼容性** - 考虑不同操作系统的兼容性

### 添加新脚本的规范
1. **命名规范** - 使用kebab-case命名（如：new-feature-deploy.sh）
2. **文档说明** - 在脚本头部添加功能说明
3. **参数支持** - 支持 `--help` 参数显示使用说明
4. **日志输出** - 使用统一的日志格式和颜色

## 🔗 相关文档

- [项目部署文档](../docs/deployment.md)
- [故障排查指南](../docs/troubleshooting.md)
- [API文档](../docs/api.md)
- [主项目README](../README.md)

---

## 💡 快速参考

| 操作 | Windows | Linux/macOS |
|------|---------|-------------|
| 前端部署 | `.\scripts\frontend-deploy.bat` | `./scripts/frontend-deploy.sh` |
| 完整部署 | `.\scripts\deploy.bat` | `./scripts/deploy.sh` |
| 健康检查 | `.\scripts\megatts3_health.bat` | `./scripts/megatts3_health.sh` |
| 查看日志 | `docker-compose logs -f` | `docker-compose logs -f` |
| 重启服务 | `docker-compose restart` | `docker-compose restart` |

**记住：所有脚本都需要在项目根目录（AI-Sound/）下运行！**

# 🚀 AI-Sound 自动化脚本工具

本目录包含AI-Sound项目的自动化脚本和开发工具。

## 📋 脚本列表

### 🛠️ 开发环境脚本

| 脚本 | 平台 | 功能 | 使用场景 |
|------|------|------|----------|
| `dev-start.bat` | Windows | 启动开发环境 | 日常开发，支持热重载 |
| `dev-start.sh` | Linux/macOS | 启动开发环境 | 日常开发，支持热重载 |
| `check-code.bat` | Windows | 检查代码同步 | 验证容器内代码是否为最新 |
| `force-rebuild.bat` | Windows | 强制重建容器 | 解决Docker缓存问题 |

### 🚀 部署脚本

| 脚本 | 平台 | 功能 | 使用场景 |
|------|------|------|----------|
| `deploy.bat` | Windows | 一键部署 | 生产环境部署 |
| `deploy.sh` | Linux/macOS | 一键部署 | 生产环境部署 |

### 🔧 维护脚本

| 脚本 | 平台 | 功能 | 使用场景 |
|------|------|------|----------|
| `maintain_megatts3.sh` | Linux/macOS | MegaTTS3维护 | 定期维护检查 |

## 🛠️ 开发环境使用

### 启动开发环境

**Windows:**
```bash
cd AI-Sound
scripts\dev-start.bat
```

**Linux/macOS:**
```bash
cd AI-Sound
chmod +x scripts/dev-start.sh
scripts/dev-start.sh
```

**功能特点：**
- ✅ 代码热重载 - 修改Python代码立即生效
- ✅ Volume挂载 - 避免Docker构建缓存问题  
- ✅ 调试模式 - 详细日志输出
- ✅ 自动检查 - 服务状态自动检测

### 检查代码同步

当修改代码后，可以验证容器内代码是否为最新：

```bash
# 检查特定代码（例如：book_id修复）
scripts\check-code.bat "book_id.*Optional"

# 检查文件时间戳
scripts\check-code.bat
```

**输出示例：**
```
[CHECK] 检查容器内代码是否更新...
[CHECK] 检查本地代码...
platform\backend\app\novel_reader.py:37:    book_id: Optional[int] = Form(None),

[CHECK] 检查容器内代码...
37:    book_id: Optional[int] = Form(None),

[CHECK] 代码同步正常！
```

### 强制重建容器

当遇到Docker缓存问题时：

```bash
scripts\force-rebuild.bat
```

**执行流程：**
1. 停止所有服务
2. 清理Docker缓存
3. 强制重新构建镜像  
4. 重新启动服务
5. 检查服务状态

## 🚀 生产环境部署

### 一键部署

**Windows:**
```bash
scripts\deploy.bat
```

**Linux/macOS:**
```bash
chmod +x scripts/deploy.sh
scripts/deploy.sh
```

**部署流程：**
1. 检查前置条件
2. 构建前端静态文件
3. 启动Docker服务
4. 等待服务就绪
5. 执行健康检查

## 🔧 维护和故障排查

### MegaTTS3维护

```bash
# Linux/macOS
chmod +x scripts/maintain_megatts3.sh
scripts/maintain_megatts3.sh
```

**维护内容：**
- 检查容器状态
- 验证API服务
- 自动重启异常服务
- 生成维护报告

### 常见问题解决

#### 1. 代码修改不生效
```bash
# 检查代码同步
scripts\check-code.bat

# 如果不同步，强制重建
scripts\force-rebuild.bat
```

#### 2. 服务启动失败
```bash
# 查看详细日志
docker-compose logs -f

# 重新部署
scripts\force-rebuild.bat
```

#### 3. 端口冲突
```bash
# 检查端口占用
netstat -tulpn | grep :3001
netstat -tulpn | grep :7929

# 停止冲突服务后重新启动
docker-compose down
scripts\dev-start.bat
```

## 📝 自定义脚本

### 添加新的开发脚本

1. 创建新脚本文件
2. 设置执行权限（Linux/macOS）
3. 更新本README文档
4. 测试脚本功能

### 脚本模板

**Windows批处理模板：**
```batch
@echo off
echo [SCRIPT] 脚本描述...

REM 检查Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker未运行
    pause
    exit /b 1
)

REM 执行主要逻辑
echo [INFO] 执行操作...

echo [SUCCESS] 操作完成！
pause
```

**Linux/macOS Shell模板：**
```bash
#!/bin/bash
echo "🔧 脚本描述..."

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装"
    exit 1
fi

# 执行主要逻辑
echo "ℹ️ 执行操作..."

echo "✅ 操作完成！"
```

## 🔗 相关文档

- [DEVELOPMENT.md](../DEVELOPMENT.md) - 详细开发指南
- [README.md](../README.md) - 项目主文档
- [Docker配置文档](../docker/README.md) - Docker相关配置