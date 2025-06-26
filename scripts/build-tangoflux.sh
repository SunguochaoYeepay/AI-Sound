#!/bin/bash
# TangoFlux独立服务构建脚本

echo "🚀 开始构建TangoFlux独立服务..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请启动Docker Desktop"
    exit 1
fi

# 构建TangoFlux镜像
echo "📦 构建TangoFlux镜像..."
docker build -f docker/tangoflux/Dockerfile -t ai-sound-tangoflux:latest .

if [ $? -eq 0 ]; then
    echo "✅ TangoFlux镜像构建成功"
    
    # 显示镜像信息
    echo "📊 镜像信息:"
    docker images | grep ai-sound-tangoflux
    
    echo ""
    echo "🎯 下一步:"
    echo "1. 运行: docker-compose up tangoflux"
    echo "2. 测试: curl http://localhost:7930/health"
    echo "3. 完整启动: docker-compose up"
else
    echo "❌ TangoFlux镜像构建失败"
    exit 1
fi 