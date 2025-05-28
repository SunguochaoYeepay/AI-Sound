# AI-Sound TTS 服务

本目录包含 AI-Sound TTS 系统的核心服务组件，包括 API 服务和 Web 管理界面。

## 系统架构

系统采用微服务架构，包含以下组件：

```
[Web Admin UI] --> [API Gateway] --> [TTS Services]
     |               |                    |
     |               |                    ├── MegaTTS3
     |               |                    ├── ESPnet
     |               |                    └── Bert-VITS2 (后续阶段)
     |               |
     |               └── [Task Management]
     └── [Audio Library]
```

各组件职责：

- **API Gateway**: 统一接口、服务发现、负载均衡
- **TTS Services**: 独立部署的语音合成引擎
- **Web Admin**: 统一的管理界面
- **Task Management**: 异步任务处理
- **Audio Library**: 音频资源管理

## 目录结构

- `api/`: 后端 API 服务
- `web-admin/`: 前端管理界面
- `docker-compose.yml`: 容器编排配置
- `create_network.bat/sh`: 创建 Docker 网络脚本
- `start_all_services.bat`: 启动所有服务脚本
- `stop_all_services.bat`: 停止所有服务脚本

## 快速启动

### 准备工作

确保已安装以下软件：

- Docker
- Docker Compose

### 启动服务

1. 执行网络创建脚本：

```bash
# Windows
create_network.bat

# Linux/Mac
./create_network.sh
```

2. 分别启动各个服务：

```bash
# 启动 MegaTTS3 服务
cd ../MegaTTS3
docker-compose up -d

# 启动 ESPnet 服务
cd ../espnet
docker-compose up -d

# 启动 API 和 Web 服务
cd ../services
docker-compose up -d
```

或者直接使用一键启动脚本：

```bash
# Windows
start_all_services.bat
```

### 访问服务

- Web 管理界面: http://localhost:8080
- API 服务: http://localhost:9930

## API 接口

### 核心接口

- `GET /health`: 健康检查
- `GET /health/engines`: 引擎健康检查
- `GET /api/engines`: 获取所有可用引擎
- `GET /api/engines/{engine_name}`: 获取特定引擎详情
- `POST /api/engines/{engine_name}/health`: 检查特定引擎健康状态
- `GET /api/voices`: 获取所有可用音色
- `POST /api/tts`: 文本转语音合成

### 引擎选择

系统支持自动选择合适的引擎，根据以下因素：

- 文本长度
- 情感需求
- 文本类型（对话/非对话）
- 用户偏好

可以通过在请求中设置 `engine` 参数来指定特定引擎：

```json
{
  "text": "要合成的文本",
  "voice_id": "female_young",
  "engine": "megatts3"  // 或 "espnet" 或 "auto"
}
```

## 故障排除

如果遇到服务无法正常通信的问题，请检查：

1. 网络配置是否正确
2. 各服务是否正常启动
3. 查看日志 `docker-compose logs -f api`