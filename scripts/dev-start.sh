#!/bin/bash
echo "🛠️ [DEV-MODE] 启动AI-Sound开发环境..."

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ [ERROR] Docker未运行，请先启动Docker"
    exit 1
fi

# 使用开发配置启动服务
echo "🚀 [DEV-MODE] 使用开发配置启动服务..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 等待服务启动
echo "⏳ [DEV-MODE] 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 [DEV-MODE] 检查服务状态..."
docker-compose ps

echo "🎉 [DEV-MODE] 服务启动完成！"
echo "ℹ️ [INFO] 前端地址: http://localhost:3001"
echo "ℹ️ [INFO] 后端API: http://localhost:3001/api"
echo "ℹ️ [INFO] 后端健康检查: http://localhost:3001/health"
echo "ℹ️ [INFO] 查看后端日志: docker logs ai-sound-backend -f" 