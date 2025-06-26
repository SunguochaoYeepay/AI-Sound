# 重建SongGeneration服务脚本
Write-Host "🔄 重建SongGeneration服务..." -ForegroundColor Green

# 切换到项目目录
Set-Location "D:\AI-Sound"

# 停止并删除现有容器
Write-Host "🛑 停止现有SongGeneration容器..." -ForegroundColor Yellow
docker stop ai-sound-songgeneration 2>$null
docker rm ai-sound-songgeneration 2>$null

# 删除旧镜像（如果存在）
Write-Host "🗑️ 清理旧镜像..." -ForegroundColor Yellow
docker rmi ai-sound_songgeneration 2>$null

# 重新构建服务
Write-Host "🔨 重新构建SongGeneration镜像..." -ForegroundColor Green
docker-compose build songgeneration

# 启动服务
Write-Host "🚀 启动SongGeneration服务..." -ForegroundColor Green
docker-compose up -d songgeneration

# 等待启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查服务状态
Write-Host "📊 检查服务状态..." -ForegroundColor Blue
docker-compose ps songgeneration

# 显示日志
Write-Host "📄 显示最新日志..." -ForegroundColor Blue
docker-compose logs --tail=20 songgeneration

Write-Host "✅ 重建完成！" -ForegroundColor Green
Write-Host "🔗 健康检查: http://localhost:8081/health" -ForegroundColor Cyan
Write-Host "🧪 测试接口: http://localhost:8081/test" -ForegroundColor Cyan 