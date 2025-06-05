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