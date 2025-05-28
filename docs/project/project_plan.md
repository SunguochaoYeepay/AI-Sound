# AI-Sound 项目计划文档

## 项目概述

AI-Sound 是一个整合多种 TTS（文本转语音）引擎的综合服务平台，旨在提供统一的 API 接口和管理界面，支持多种 TTS 引擎的无缝切换和协同工作。

## 系统架构

系统采用微服务架构，主要包含以下组件：

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

## 已完成工作

### 第一阶段：基础架构搭建（已完成）

1. **Docker 化现有 TTS 引擎**
   - [x] MegaTTS3 Docker 化
   - [x] ESPnet Docker 化
   - [ ] Bert-VITS2 Docker 化（推迟到后续阶段）

2. **网络架构设计**
   - [x] 创建统一的 Docker 网络（ai-sound-network）
   - [x] 配置服务间通信路由
   - [x] 配置健康检查机制

3. **适配器层实现**
   - [x] 定义统一的 TTSEngine 接口
   - [x] 实现 MegaTTS3Adapter
   - [x] 实现 ESPnetAdapter
   - [x] 实现引擎路由器（TTSEngineRouter）
   - [x] 实现引擎选择策略（EngineSelector）
   - [x] 实现服务监控（ServiceMonitor）

4. **API 网关扩展**
   - [x] 扩展 API 接口支持多引擎路由
   - [x] 添加引擎健康检查端点
   - [x] 添加引擎管理端点
   - [x] 添加音色查询端点

5. **部署与测试工具**
   - [x] 创建模拟服务（用于开发和测试）
   - [x] 编写启动/停止脚本
   - [x] 添加网络创建脚本
   - [x] 编写详细文档

## 当前状态

- API 网关能够成功连接到 MegaTTS3 和 ESPnet 服务
- 健康检查功能正常工作
- 引擎选择策略根据文本特征选择合适的引擎
- 服务监控定期检查引擎健康状态
- 部署脚本和工具已完成
- Web管理界面已实现引擎状态可视化面板，可监控MegaTTS3和ESPnet引擎健康状态

## 下一阶段计划

### 第二阶段：功能扩展（计划中）

1. **Web 管理界面增强**
   - [x] 添加引擎状态可视化面板
   - [ ] 实现引擎参数配置界面
   - [ ] 添加音色管理功能

2. **Bert-VITS2 集成**
   - [ ] Bert-VITS2 Docker 化
   - [ ] 实现 Bert-VITS2Adapter
   - [ ] 扩展引擎选择策略支持 Bert-VITS2

3. **高级功能**
   - [ ] 批量处理优化
   - [ ] 任务队列管理
   - [ ] 用户偏好记忆
   - [ ] 自适应引擎选择算法优化

4. **监控与日志**
   - [ ] 添加详细的性能监控
   - [ ] 实现集中式日志管理
   - [ ] 添加告警机制

## 部署要求

### 硬件要求

- **推荐配置**：
  - CPU: 8+ 核心
  - RAM: 16GB+
  - GPU: NVIDIA GPU with 8GB+ VRAM (支持 CUDA)
  - 存储: 50GB+ SSD

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (用于 GPU 支持)
- Python 3.8+ (本地开发)

## 使用说明

### 启动服务

1. 创建共享网络:
```bash
./services/create_network.sh  # Linux/Mac
# 或
services\create_network.bat  # Windows
```

2. 启动所有服务:
```bash
./services/start_all_services.sh  # Linux/Mac
# 或
services\start_all_services.bat  # Windows
```

### 访问服务

- Web 管理界面: http://localhost:8080
- API 服务: http://localhost:9930

## 已知问题与解决方案

1. **Docker 容器无法连接到宿主机服务**
   - 解决方案: 在 docker-compose.yml 中使用 `extra_hosts` 设置 host.docker.internal

2. **模拟服务与真实服务的差异**
   - 当前模拟服务仅提供基本功能，与真实服务可能存在差异
   - 建议在生产环境中使用真实 TTS 引擎服务

## 项目维护

- 每月更新依赖
- 每季度进行一次全面测试
- 保持文档与代码同步更新