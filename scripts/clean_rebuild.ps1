# AI-Sound 彻底清理重建脚本
# 老爹专用 - 永远不会再出现构建问题！

Write-Host "🔥 开始彻底清理..." -ForegroundColor Red

# 停止所有服务
Write-Host "📦 停止所有容器..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down

# 删除所有相关镜像
Write-Host "🗑️  删除AI-Sound相关镜像..." -ForegroundColor Yellow
docker images | findstr ai-sound | ForEach-Object { 
    $imageId = ($_ -split '\s+')[2]
    docker rmi $imageId -f
}

# 清理构建缓存
Write-Host "🧹 清理Docker构建缓存..." -ForegroundColor Yellow
docker builder prune -f

# 重新构建（强制无缓存）
Write-Host "🚀 重新构建所有服务（无缓存）..." -ForegroundColor Green
docker-compose -f docker-compose.prod.yml build --no-cache

# 启动服务
Write-Host "▶️  启动所有服务..." -ForegroundColor Green
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# 检查服务状态
Write-Host "✅ 检查服务状态..." -ForegroundColor Green
docker ps

Write-Host "🎉 清理重建完成！如果还有问题，老爹可以直接发飙了！" -ForegroundColor Green 