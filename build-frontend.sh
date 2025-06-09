#!/bin/bash

echo "开始构建前端..."

# 进入前端目录
cd platform/frontend

# 检查Node.js环境
if command -v node &> /dev/null; then
    echo "使用本地Node.js构建"
    npm run build
elif command -v docker &> /dev/null; then
    echo "使用Docker构建"
    docker run --rm -v "$(pwd):/app" -w /app node:18-alpine sh -c "npm install && npm run build"
else
    echo "错误：未找到Node.js或Docker环境"
    exit 1
fi

echo "前端构建完成"
echo "重启nginx容器..."
docker restart ai-sound-nginx
echo "构建完成！" 