# AI-Sound

AI-Sound 是一个统一管理多种 TTS（文本转语音）引擎的综合平台，提供无缝整合的语音合成服务。

## 项目特点

- **多引擎支持**：整合 MegaTTS3、ESPnet 和 Bert-VITS2（计划中）
- **统一 API**：提供标准化接口，简化集成过程
- **智能引擎选择**：根据文本特征自动选择最合适的引擎
- **服务监控**：实时监控各引擎的健康状态
- **Docker 化部署**：简化安装和扩展过程

## 快速开始

### 安装要求

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (用于 GPU 支持)

### 启动服务

1. 克隆仓库：
```bash
git clone https://github.com/your-org/ai-sound.git
cd ai-sound
```

2. 创建共享网络：
```bash
# Windows
services\create_network.bat

# Linux/Mac
./services/create_network.sh
```

3. 启动服务：
```bash
# Windows
services\start_all_services.bat

# Linux/Mac
./services/start_all_services.sh
```

### 访问服务

- Web 管理界面：http://localhost:8080
- API 服务：http://localhost:9930

## 项目文档

详细文档请参阅：

- [项目计划](docs/general/PROJECT_PLAN.md)
- [开发者指南](docs/general/DEVELOPER_GUIDE.md)
- [更新日志](docs/general/CHANGELOG.md)
- [整合计划](docs/integration/integration_plan.md)
- [技术细节](docs/integration/technical/technical_details.md)

## API 使用示例

```python
import requests

# 基本合成请求
response = requests.post("http://localhost:9930/api/v1/synthesize", json={
    "text": "欢迎使用AI-Sound服务。",
    "voice_id": "female_001",
    "engine": "auto"  # 自动选择引擎
})

# 保存音频文件
with open("output.wav", "wb") as f:
    f.write(response.content)
```

## 项目状态

当前版本：0.1.0

已完成：
- 基础架构搭建
- MegaTTS3 和 ESPnet 引擎整合
- API 网关实现
- 服务监控实现

计划中：
- Bert-VITS2 引擎整合
- Web 管理界面增强
- 高级任务管理
- 性能优化

## 贡献指南

欢迎贡献！请参阅[开发者指南](docs/general/DEVELOPER_GUIDE.md)了解更多信息。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件