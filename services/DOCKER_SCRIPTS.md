# Docker管理脚本说明

## 📁 脚本清单

### 🔨 构建脚本
- **`build_api.bat`** - 标准API构建脚本
  - 使用docker-compose build
  - 支持多镜像源备选
  - 自动测试构建结果

### 🧹 清理脚本  
- **`clean_docker.bat`** - Docker环境清理
  - 清理所有缓存、容器、镜像
  - 释放磁盘空间
  - 显示清理结果

### 🧪 测试脚本
- **`test_health_simple.py`** - API健康检查测试
  - 测试基础API功能
  - 验证引擎健康检查
  - 显示详细错误信息

### 🚀 开发调试脚本
- **`dev_mode.bat`** - 开发模式启动（推荐）
  - 代码热重载，修改即生效
  - 无需重新构建Docker镜像
  - 支持前后端同时开发

- **`quick_debug.bat`** - 快速调试重启
  - 仅重启API服务
  - 保留数据库和其他服务
  - 适合后端代码调试

- **`local_dev.bat`** - 本地开发模式
  - 完全脱离Docker运行
  - 直接使用本地Python环境
  - 最快的开发调试方式

## 🚀 使用流程

### 生产环境部署
```bash
# 1. 清理Docker环境（可选）
clean_docker.bat

# 2. 构建API服务
build_api.bat

# 3. 测试API功能（可选）
python test_health_simple.py
```

### 开发调试流程
```bash
# 方案1: 开发模式（推荐）
dev_mode.bat
# 修改代码后自动重载，无需重启

# 方案2: 快速调试
quick_debug.bat
# 仅重启API服务，速度较快

# 方案3: 本地开发
local_dev.bat
# 完全本地运行，调试最方便
```

## 📝 注意事项

### 开发模式优势
- ✅ 代码修改即时生效
- ✅ 无需重新构建镜像
- ✅ 保留Docker环境一致性
- ✅ 支持断点调试

### 本地开发优势
- ✅ 启动速度最快
- ✅ 调试功能最全
- ✅ 无Docker缓存问题
- ⚠️ 需要本地安装依赖

### 选择建议
- **日常开发**: 使用 `dev_mode.bat`
- **快速修复**: 使用 `quick_debug.bat`  
- **深度调试**: 使用 `local_dev.bat`
- **生产部署**: 使用 `build_api.bat` 