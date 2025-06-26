# SongGeneration Docker 快速启动指南

## 🚀 **一键启动**

```bash
# 1. 进入项目目录
cd D:\AI-Sound\MegaTTS\Song-Generation

# 2. 启动Docker服务
docker-compose up -d

# 3. 查看启动日志
docker logs songgeneration-service -f
```

## ⏱️ **启动时间线**

```
0-30秒    : Docker容器启动
30秒-3分钟 : Python环境初始化
3-8分钟    : 模型加载（11GB主模型 + 组件）
8分钟后    : 服务就绪，可以访问
```

## 🌐 **访问地址**

| 服务 | 地址 | 说明 |
|------|------|------|
| **API服务** | http://localhost:7862 | 主要访问地址 |
| **API文档** | http://localhost:7862/docs | FastAPI自动生成的文档 |
| **健康检查** | http://localhost:7862/health | 服务状态检查 |

## 📊 **状态检查命令**

```bash
# 查看容器状态
docker ps | grep songgeneration

# 查看资源使用
docker stats songgeneration-service --no-stream

# 查看GPU使用
docker exec songgeneration-service nvidia-smi

# 查看端口监听
docker exec songgeneration-service netstat -tlnp
```

## 🔧 **常用操作**

### **重启服务**
```bash
docker-compose restart
```

### **停止服务**
```bash
docker-compose down
```

### **查看日志**
```bash
# 实时日志
docker logs songgeneration-service -f

# 最新50行日志
docker logs songgeneration-service --tail 50
```

### **进入容器**
```bash
docker exec -it songgeneration-service bash
```

## 🎵 **测试API**

### **健康检查**
```bash
curl http://localhost:7862/health
```

### **生成音乐（示例）**
```bash
curl -X POST "http://localhost:7862/api/songgeneration" \
     -H "Content-Type: application/json" \
     -d '{
       "lyrics": "夏天的风轻轻吹过",
       "genre": "pop",
       "duration": 30
     }'
```

## 🚨 **故障排除**

### **问题1：页面无法访问**
```bash
# 检查端口是否监听
docker exec songgeneration-service netstat -tlnp | grep 7862

# 如果没有，说明模型还在加载，继续等待
docker logs songgeneration-service --tail 10
```

### **问题2：模型加载失败**
```bash
# 检查GPU状态
docker exec songgeneration-service nvidia-smi

# 检查模型文件
docker exec songgeneration-service ls -la /app/ckpt/ckpt/songgeneration_base/model.pt
```

### **问题3：内存不足**
```bash
# 查看内存使用
docker stats songgeneration-service

# 重启释放内存
docker-compose restart
```

## 📈 **性能优化**

### **GPU模式确认**
```bash
# 确保GPU可用
docker exec songgeneration-service nvidia-smi

# 确保Docker GPU支持
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### **避免频繁重启**
- 模型加载时间长，尽量避免重启
- 使用 `docker pause/unpause` 替代 `stop/start`
- 定期检查日志，预防问题

## 🔄 **更新流程**

### **更新代码**
```bash
# 1. 修改代码文件
# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 重启服务
docker-compose up -d
```

### **更新模型**
```bash
# 1. 替换 ckpt/ 目录下的模型文件
# 2. 重启容器
docker-compose restart
```

---

**提示**: 首次启动请耐心等待3-8分钟，这是正常的大模型加载时间！ 🎵 