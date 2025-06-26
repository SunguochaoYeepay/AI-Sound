# SongGeneration Docker化项目说明

## 📋 **项目概述**

本项目是基于腾讯官方SongGeneration音乐生成模型的Docker化部署版本。

### **项目来源**
- **官方仓库**: https://github.com/tencent/SongGeneration
- **官方模型**: HuggingFace上的`tencent/SongGeneration`
- **Fork时间**: 2025年6月
- **改造目的**: 为AI-Sound平台提供本地化的音乐生成服务

## 🐳 **Docker化改造过程**

### **架构选择**
- **基础镜像**: `juhayna/song-generation-levo:hf0613` (24.5GB预配置环境)
- **模型文件**: 本地Volume挂载 `./ckpt:/app/ckpt:ro`
- **GPU支持**: NVIDIA RTX 4090 通过Docker GPU配置

### **主要修改内容**

#### **1. 代码修改**
- **api_server.py**: 添加CPU/GPU自适应支持
- **导入路径**: 修复`from model_septoken import`为相对导入
- **设备检测**: 自动检测CUDA可用性，兼容CPU/GPU环境

#### **2. 删除的文件**
以下文件在Docker化后不再需要，已清理：

**虚拟环境** (节省10.3GB):
- `venv_songgen/` - Python虚拟环境
- `venv_songgen310/` - 另一个虚拟环境

**多余的构建文件**:
- `Dockerfile` - 原始Dockerfile
- `Dockerfile.clean` - 清理版本
- `Dockerfile.local` - 本地版本
- `Dockerfile.minimal` - 最小版本
- `Dockerfile.simple` - 简单版本
- `Dockerfile.simple2` - 简单版本2

**多余的依赖文件**:
- `requirements_full.txt` - 完整依赖
- `requirements_local.txt` - 本地依赖
- `requirements_minimal.txt` - 最小依赖
- `requirements_safe.txt` - 安全版本依赖
- `requirements_temp.txt` - 临时依赖

**测试和临时文件**:
- `simple_api_server.py` - 简化API服务器
- `simple_api_test.py` - API测试
- `test_api_health.py` - 健康检查测试
- `test_server.py` - 服务器测试
- `generate.py` - 生成脚本
- `generate_lowmem.py` - 低内存生成脚本
- `main_integrated.py` - 集成主程序
- `custom_demo.py` - 自定义演示
- `generate.sh` - Shell生成脚本
- `generate_lowmem.sh` - 低内存Shell脚本
- `run_docker.bat` - Docker运行批处理

## 📁 **当前文件结构**

### **核心文件**
- `api_server.py` - 主API服务器（已修改）
- `docker-compose.yml` - Docker编排配置
- `Dockerfile.official` - Docker构建文件
- `requirements.txt` - 主要Python依赖
- `requirements_docker.txt` - Docker专用依赖

### **目录说明**
- `ckpt/` (61GB) - 模型权重文件，通过Volume挂载
- `codeclm/` - 核心模型代码
- `third_party/` - 第三方依赖库
- `tools/` - 工具脚本（包含Gradio工具）
- `templates/` - HTML模板文件
- `sample/` - 示例文件和描述
- `output/` - 生成的音乐输出
- `img/` - 界面图片资源

## 🚀 **部署方式**

### **启动服务**
```bash
docker-compose up -d
```

### **访问地址**
- **API服务**: http://localhost:7862
- **API文档**: http://localhost:7862/docs
- **DEMO页面**: http://localhost:7862 (HTML界面)

### **模型加载时间**
- **首次启动**: 3-8分钟（需要加载11GB主模型）
- **后续重启**: 同样时间（Docker重启会清空内存）
- **建议**: 避免频繁重启容器

## 🔧 **技术细节**

### **GPU配置**
- **显卡要求**: NVIDIA RTX 4090 (24GB显存)
- **GPU使用**: 约9.5GB显存用于模型推理
- **CUDA版本**: 12.8

### **性能表现**
- **CPU模式**: 150%+ CPU使用率，23GB+ 内存（容易崩溃）
- **GPU模式**: 7-15% CPU使用率，4GB内存（稳定运行）

### **存储需求**
- **模型文件**: 61GB (本地存储)
- **Docker镜像**: 24.5GB (官方基础镜像)
- **运行内存**: 4-8GB RAM + 9.5GB GPU显存

## 📝 **维护说明**

### **更新模型**
- 直接替换`ckpt/`目录下的模型文件
- 重启Docker容器生效

### **修改代码**
- 编辑源代码文件
- 重新构建Docker镜像: `docker-compose build`

### **日志查看**
```bash
docker logs songgeneration-service -f
```

### **性能监控**
```bash
docker stats songgeneration-service
```

## ⚠️ **注意事项**

1. **首次启动时间长**: 模型加载需要3-8分钟，属于正常现象
2. **避免频繁重启**: 每次重启都需要重新加载模型
3. **GPU必需**: CPU模式不稳定，强烈建议使用GPU
4. **存储空间**: 确保有足够磁盘空间存储模型和镜像

## 📊 **项目状态**

- ✅ **Docker化完成**: 成功基于官方镜像构建
- ✅ **GPU支持**: RTX 4090正常工作
- ✅ **API服务**: FastAPI接口正常
- ✅ **模型加载**: 11GB主模型正常加载
- ✅ **代码清理**: 删除无用文件，节省10.3GB空间

---

**最后更新**: 2025年6月26日  
**版本**: Docker化版本v1.0  
**维护者**: AI-Sound团队 