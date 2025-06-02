# 🐳 MegaTTS3 Enhanced API - Docker增强部署指南

## **📋 概述**

这是一个专为现有Docker环境设计的MegaTTS3 Enhanced API增强部署方案，提供生产级的API服务、监控和管理功能。

---

## **🚀 快速部署**

### **1. 环境检查**
```bash
# 检查Docker环境
python deploy-docker-enhanced.py --check-only
```

### **2. 一键部署**
```bash
# 执行完整部署
python deploy-docker-enhanced.py
```

### **3. 访问服务**
部署完成后，可以通过以下地址访问：

- **Enhanced API**: http://localhost:7929
- **API网关**: http://localhost:8080  
- **Prometheus监控**: http://localhost:9091
- **Grafana面板**: http://localhost:3000 (admin/admin123)
- **API指标**: http://localhost:7929/metrics

---

## **🏗️ 架构组件**

### **核心服务**

| 服务 | 端口 | 功能 | 容器名 |
|------|------|------|--------|
| Enhanced API | 7929 | 主语音合成服务 | megatts-enhanced-api |
| Nginx网关 | 8080 | API网关和负载均衡 | megatts-nginx |
| Prometheus | 9091 | 指标收集 | megatts-prometheus |
| Grafana | 3000 | 监控面板 | megatts-grafana |
| Redis | 6379 | 缓存服务 | megatts-redis |

### **增强特性**
- ✅ **生产级API**: FastAPI + 异步处理
- ✅ **真实推理引擎**: 多进程MegaTTS3集成
- ✅ **指标监控**: Prometheus + Grafana
- ✅ **结构化日志**: JSON格式 + 轮转
- ✅ **健康检查**: 自动重启 + 状态监控
- ✅ **缓存优化**: Redis缓存层

---

## **🔧 手动管理**

### **Docker Compose命令**
```bash
# 启动所有服务
docker-compose -f docker-deploy-enhanced.yml up -d

# 查看服务状态
docker-compose -f docker-deploy-enhanced.yml ps

# 查看日志
docker-compose -f docker-deploy-enhanced.yml logs -f megatts-enhanced

# 停止所有服务
docker-compose -f docker-deploy-enhanced.yml down

# 重启特定服务
docker-compose -f docker-deploy-enhanced.yml restart megatts-enhanced
```

### **单容器管理**
```bash
# 查看Enhanced API日志
docker logs megatts-enhanced-api -f

# 进入容器
docker exec -it megatts-enhanced-api /bin/bash

# 重启API服务
docker restart megatts-enhanced-api

# 查看容器资源使用
docker stats megatts-enhanced-api
```

---

## **📊 API使用示例**

### **健康检查**
```bash
curl http://localhost:7929/health
curl http://localhost:8080/health  # 通过网关
```

### **获取API信息**
```bash
curl http://localhost:7929/info
```

### **上传声音对**
```bash
curl -X POST http://localhost:7929/api/voice-pairs/upload \
  -F "name=test_voice" \
  -F "wav_file=@reference.wav" \
  -F "npy_file=@reference.npy"
```

### **语音合成**
```bash
curl -X POST http://localhost:7929/api/synthesis/by-paths \
  -H "Content-Type: application/json" \
  -d '{
    "wav_file_path": "/app/storage/voices/test_voice.wav",
    "npy_file_path": "/app/storage/voices/test_voice.npy", 
    "text": "你好，这是一个测试。"
  }'
```

### **获取指标**
```bash
curl http://localhost:7929/metrics
```

---

## **📈 监控与告警**

### **Prometheus指标**
访问 http://localhost:9091 查看以下关键指标：

- `http_requests_total` - HTTP请求总数
- `inference_duration_seconds` - 推理耗时
- `inference_queue_size` - 推理队列长度
- `voice_pairs_total` - 声音对数量
- `system_cpu_percent` - CPU使用率

### **Grafana面板**
访问 http://localhost:3000 (admin/admin123) 查看：

- API性能监控
- 推理引擎状态
- 系统资源使用
- 业务指标统计

---

## **🔍 故障排查**

### **常见问题**

#### **1. API无响应**
```bash
# 检查容器状态
docker ps | grep megatts

# 查看API日志
docker logs megatts-enhanced-api

# 检查模型文件
docker exec megatts-enhanced-api ls -la /app/checkpoints/
```

#### **2. 推理失败**
```bash
# 检查GPU可用性
docker exec megatts-enhanced-api nvidia-smi

# 查看推理日志
docker logs megatts-enhanced-api | grep inference

# 检查存储空间
docker exec megatts-enhanced-api df -h
```

#### **3. 监控服务不可用**
```bash
# 重启监控服务
docker-compose -f docker-deploy-enhanced.yml restart prometheus-lite grafana-lite

# 检查网络连接
docker network ls | grep ai-sound
```

### **日志查看**
```bash
# 所有服务日志
docker-compose -f docker-deploy-enhanced.yml logs

# 特定服务日志
docker-compose -f docker-deploy-enhanced.yml logs megatts-enhanced

# 实时日志跟踪
docker-compose -f docker-deploy-enhanced.yml logs -f --tail=100
```

---

## **🔒 安全配置**

### **默认安全措施**
- ✅ 非root用户运行
- ✅ 网络隔离
- ✅ 资源限制
- ✅ 健康检查
- ✅ 自动重启

### **生产环境建议**
1. **启用HTTPS**: 配置SSL证书
2. **API认证**: 启用API密钥验证
3. **访问控制**: 配置防火墙规则
4. **数据备份**: 定期备份声音对数据
5. **日志审计**: 启用访问日志分析

---

## **📝 配置文件说明**

### **主要配置文件**
- `docker-deploy-enhanced.yml` - Docker Compose配置
- `Dockerfile.enhanced` - Enhanced API镜像
- `docker-entrypoint.sh` - 容器启动脚本
- `nginx/nginx-lite.conf` - Nginx网关配置
- `monitoring/prometheus-lite.yml` - Prometheus配置

### **环境变量**
可在`docker-deploy-enhanced.yml`中修改：

```yaml
environment:
  - API_HOST=0.0.0.0
  - API_PORT=7929
  - INFERENCE_WORKERS=2
  - LOG_LEVEL=info
  - ENABLE_METRICS=true
```

---

## **🚀 扩展部署**

### **增加API实例**
```yaml
# 在docker-deploy-enhanced.yml中添加
megatts-enhanced-2:
  # ... 复制megatts-enhanced配置
  ports:
    - "7930:7929"  # 使用不同端口
```

### **启用GPU支持**
```yaml
# 添加GPU配置
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

---

**🎉 现在你拥有了一个完整的Docker化MegaTTS3 Enhanced API平台！**