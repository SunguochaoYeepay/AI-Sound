#!/bin/bash
# 前端构建脚本

echo "🔨 开始构建前端..."

# 进入前端目录
cd platform/frontend

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 构建
echo "🚀 执行构建..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 前端构建完成!"
else
    echo "❌ 前端构建失败!"
fi

# 返回根目录
cd ../.. 