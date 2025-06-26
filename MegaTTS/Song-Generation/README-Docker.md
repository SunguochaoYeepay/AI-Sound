# SongGeneration Docker 部署指南

## 🚀 快速启动

### 方法1：使用启动脚本（推荐）
```bash
# Windows
./run_docker.bat

# 或手动运行
docker-compose up -d
```

### 方法2：手动构建和运行
```bash
# 构建镜像（轻量化，不包含模型文件）
docker build -t songgeneration:latest .

# 运行容器（挂载本地模型文件）
docker run -d \
  --name songgeneration \
  -p 7862:7862 \
  -v ./output:/app/output \
  -v ./temp:/app/temp \
  -v ./ckpt:/app/ckpt:ro \
  songgeneration:latest
```

## 📝 API 接口

服务启动后，访问 `http://localhost:7862`

### 主要端点
- `GET /` - 服务信息
- `GET /health` - 健康检查
- `GET /supported_genres` - 支持的音乐风格
- `POST /generate` - 生成歌曲
- `POST /generate_with_audio` - 使用音频提示生成
- `GET /download/{file_id}` - 下载生成的歌曲

### 生成歌曲示例
```bash
curl -X POST "http://localhost:7862/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "lyrics": "星空下的梦想，照亮前行的路",
    "descriptions": "温柔的民谣风格",
    "auto_prompt_audio_type": "Folk",
    "cfg_coef": 1.5,
    "temperature": 0.9,
    "top_k": 50
  }'
```

## 🔧 管理命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看容器状态
docker-compose ps

# 进入容器
docker exec -it songgeneration-service bash
```

## 📊 系统要求

- **内存**: 建议8GB以上
- **存储**: Docker镜像约2GB（模型文件通过volume挂载，不占用镜像空间）
- **GPU**: 支持CUDA（可选，CPU也能运行但较慢）

## 💡 volume挂载方式优势

- ✅ **镜像轻量化**: 不将几GB模型文件打包进镜像
- ✅ **快速构建**: 构建时间大大缩短  
- ✅ **模型共享**: 多个容器可共享同一份模型文件
- ✅ **便于更新**: 更新模型文件无需重建镜像

## 🔍 故障排除

### 1. 容器启动失败
```bash
# 查看详细错误
docker-compose logs

# 检查模型文件
docker exec -it songgeneration-service ls -la /app/ckpt/
```

### 2. GPU支持
如果有NVIDIA GPU，需要安装nvidia-docker2：
```bash
# 在docker-compose.yml中取消注释GPU配置
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

### 3. 端口冲突
修改docker-compose.yml中的端口映射：
```yaml
ports:
  - "8000:7862"  # 改为其他端口
```

### 4. 内存不足
减少并发生成或增加系统内存。

## 📁 文件结构

```
Song-Generation/
├── Dockerfile              # Docker镜像配置
├── docker-compose.yml      # Docker编排配置
├── .dockerignore           # Docker忽略文件
├── run_docker.bat         # Windows启动脚本
├── requirements_temp.txt   # Python依赖
├── api_server.py          # API服务器
├── ckpt/                  # 模型文件目录
│   └── songgeneration_base/
├── output/                # 生成的音乐文件
└── temp/                  # 临时文件
```

## 🎵 支持的音乐风格

- Pop (流行)
- R&B  
- Dance (舞曲)
- Jazz (爵士)
- Folk (民谣)
- Rock (摇滚)
- Chinese Style (中国风)
- Chinese Tradition (国风)
- Metal (金属)
- Reggae (雷鬼)
- Chinese Opera (戏曲)
- Auto (自动选择)

## ⚡ 性能优化

1. **GPU加速**: 确保正确配置CUDA环境
2. **内存管理**: 避免同时处理过多请求
3. **存储优化**: 定期清理output目录中的旧文件
4. **网络配置**: 如果部署到服务器，确保防火墙开放7862端口

## 🔗 集成到AI-Sound

生成的API可以集成到AI-Sound主系统：
```python
# 在AI-Sound中调用
import requests

response = requests.post("http://localhost:7862/generate", json={
    "lyrics": "歌词内容",
    "descriptions": "风格描述",
    "auto_prompt_audio_type": "Folk"
})

if response.json()["success"]:
    file_id = response.json()["file_id"]
    # 下载生成的音乐
    audio_response = requests.get(f"http://localhost:7862/download/{file_id}")
``` 