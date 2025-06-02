# 🎵 AI-Sound

AI-Sound 是一个统一管理多种 TTS（文本转语音）引擎的综合平台，提供无缝整合的语音合成服务。

## ✨ 项目特点

- **🚀 多引擎支持**：整合 MegaTTS3、ESPnet 和 Bert-VITS2（计划中）
- **🔗 统一 API**：提供标准化接口，简化集成过程
- **🧠 智能引擎选择**：根据文本特征自动选择最合适的引擎
- **📊 服务监控**：实时监控各引擎的健康状态
- **🐳 Docker 化部署**：简化安装和扩展过程

## 🔥 当前状态

### ✅ 已运行服务
- **MegaTTS3 API 服务**：`http://localhost:7929` - GPU加速，完全可用
- **API 文档服务**：`http://localhost:8888` - 交互式文档和演示

### 📂 项目结构（已优化）
```
AI-Sound/
├── 📘 README.md                    # 项目主文档
├── 📋 CHANGELOG.md                 # 更新日志
├── 🎯 MegaTTS/MegaTTS3/           # 核心TTS服务（GPU运行）
├── 🔧 services/                    # 微服务架构
├── 🛠️ tools/                       # 工具目录
├── 📚 docs/                        # 项目文档
├── 💾 data/                        # 数据目录
├── 🗃️ archive/                     # 历史文件归档
└── 🐳 docker-compose.*.yml         # Docker配置
```

## 🚀 快速开始

### 📋 安装要求

- Docker 20.10+
- NVIDIA Container Toolkit (用于 GPU 支持)
- Python 3.8+ (用于本地文档服务)

### ⚡ 启动 MegaTTS3 服务

#### 方法一：Docker 服务（推荐）
```bash
# 启动GPU加速的API服务
docker run -d --name megatts3-api --gpus all -p 7929:7929 \
  -v "D:\AI-Sound\MegaTTS\MegaTTS3:/app" \
  -e CUDA_VISIBLE_DEVICES=0 megatts3:latest tail -f /dev/null

# 安装依赖并启动API
docker exec megatts3-api pip install flask flask-cors
docker exec -d megatts3-api bash -c "cd /app; python api_server.py"
```

#### 方法二：本地文档服务
```bash
cd MegaTTS\MegaTTS3
python start_api_demo.py
```

### 🌐 访问服务

- **🎵 TTS API 服务**：http://localhost:7929
  - 健康检查：`GET /health`
  - 语音合成：`POST /synthesize`
  
- **📖 API 文档**：http://localhost:8888
  - 完整文档：`/api_docs.html`
  - 交互演示：`/api_demo_page.html`

## 💻 API 使用示例

### Python 调用示例
```python
import requests
import json

# 健康检查
health = requests.get("http://localhost:7929/health")
print("服务状态:", health.json())

# 语音合成
response = requests.post("http://localhost:7929/synthesize", 
    json={
        "text": "欢迎使用AI-Sound MegaTTS3服务！",
        "speaker": "female_calm",
        "language": "zh"
    }
)

# 保存音频文件
if response.status_code == 200:
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("✅ 音频生成成功！")
```

### cURL 调用示例
```bash
# 健康检查
curl http://localhost:7929/health

# 语音合成
curl -X POST http://localhost:7929/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，世界！","speaker":"female_calm","language":"zh"}' \
  --output output.wav
```

## 🔧 项目管理

### 🧹 最近更新
- ✅ 项目清理完成：归档28个历史文件
- ✅ 目录结构优化：精简到19个核心文件
- ✅ MegaTTS3服务稳定运行：GPU加速支持
- ✅ 完整API文档：交互式演示页面

### 📊 服务状态检查
```bash
# 检查Docker容器
docker ps -a

# 检查端口占用
netstat -ano | findstr :7929
netstat -ano | findstr :8888

# 快速健康检查
curl http://localhost:7929/health
```

## 🎯 未来规划

### 短期目标
- [ ] 集成更多语音模型
- [ ] 完善错误处理机制
- [ ] 性能监控面板
- [ ] 批量处理接口

### 长期目标
- [ ] Bert-VITS2 引擎整合
- [ ] 多语言支持增强
- [ ] 实时语音流处理
- [ ] 云端部署方案

## 🗂️ 项目文档

- [📋 更新日志](CHANGELOG.md)
- [📁 启动指南](MegaTTS/MegaTTS3/启动指南.md)
- [🗃️ 项目清理计划](项目清理计划.md)

## 🤝 贡献指南

欢迎贡献代码！请确保：
1. 遵循现有代码风格
2. 测试新功能
3. 更新相关文档
4. 不影响MegaTTS3核心服务

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**🎉 AI-Sound - 让语音合成更简单！**