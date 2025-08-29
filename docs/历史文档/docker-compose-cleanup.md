# Docker Compose 服务清理说明

## 变更概述

为了避免端口冲突和服务重复，对 AI-Sound 项目的 Docker 服务架构进行了重要调整。

## 移除的服务

### 1. ai-sound-songgeneration 服务
- **原因**: 与独立的 `songgeneration-service` 容器重复
- **影响**: 移除了 Docker Compose 中的音乐生成服务定义
- **替代方案**: 使用独立运行的 `songgeneration-service` 容器 (端口7862)

## 修改详情

### docker-compose.yml 变更:
1. **注释掉 songgeneration 服务定义**
2. **移除后端对 songgeneration 的依赖**
3. **移除 SONGGENERATION_URL 环境变量**

### nginx.conf 变更:
1. **注释掉 songgeneration_service upstream**
2. **注释掉 /api/v1/music/ 代理配置**
3. **注释掉 /health/music 健康检查**

## 当前服务架构

### Docker Compose 管理的服务:
- `ai-sound-backend`: 8000 (可选，与本地开发互斥)
- `ai-sound-db`: 5432
- `ai-sound-redis`: 6379
- `ai-sound-megatts3`: 7929
- `ai-sound-tangoflux`: 7930
- `ai-sound-nginx`: 3001

### 独立运行的服务:
- `songgeneration-service`: 7862 (音乐生成)

### 本地开发服务:
- 本地后端: 8001 (避免与Docker后端冲突)
- 本地前端: 3000

## 优势

1. **避免端口冲突**: 本地开发和Docker服务可以并存
2. **服务解耦**: 音乐生成服务独立运行，更灵活
3. **部署简化**: 减少Docker Compose的复杂度
4. **维护便利**: 避免重复服务带来的困扰

## 注意事项

- 音乐生成功能现在由独立的 `songgeneration-service` 容器提供
- nginx 配置已相应调整，不再代理老版本的音乐生成接口
- 后端 API 通过本地化的 SongGeneration 服务处理音乐生成请求

---
**更新时间**: 2025-06-27
**修改人**: AI Assistant 