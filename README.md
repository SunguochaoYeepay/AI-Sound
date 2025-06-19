# 🎵 AI-Sound

AI-Sound 是一个基于 MegaTTS3 的企业级语音合成平台，提供高质量的语音克隆和多角色朗读服务。

> 🚀 **新手开发者？** 查看 [快速开始指南](QUICK_START.md) 5分钟上手开发！

## ✨ 项目特点

- **🚀 MegaTTS3引擎**：集成最新的 MegaTTS3 语音合成引擎
- **🎭 智能角色分配**：基于角色名称自动分配合适的声音类型
- **📖 多角色朗读**：支持小说文本的智能分段和多角色语音合成
- **🎵 音频资源库**：统一管理所有生成的音频文件
- **📊 实时监控**：完善的系统状态监控和日志记录
- **🐳 容器化部署**：支持Docker一键部署，生产环境就绪

## 🚀 快速开始

### 前置要求
- Docker 20.0+
- Docker Compose 2.0+
- 系统内存 ≥ 8GB（MegaTTS3模型需要）
- 磁盘空间 ≥ 20GB
- NVIDIA GPU（可选，用于MegaTTS3加速）

### 🛠️ 开发环境启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/AI-Sound.git
cd AI-Sound

# 2. 创建数据目录
mkdir -p data/{audio,database,logs,uploads,voice_profiles,cache,config,backups,temp}

# 3. 构建前端静态文件
cd platform/frontend
npm install
npm run build
cd ../..

# 4. 启动开发环境
scripts\dev-start.bat    # Windows
# 或 scripts/dev-start.sh  # Linux/macOS
```

### 🎯 生产环境部署

```bash
# 启动生产环境
docker-compose up -d

# 检查服务状态
docker-compose ps
curl http://localhost:3001/api/health
```

## 🙏 致谢

- [MegaTTS3](https://github.com/MegaTTS3/MegaTTS3) - 核心语音合成引擎
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Ant Design Vue](https://antdv.com/) - 企业级UI组件库