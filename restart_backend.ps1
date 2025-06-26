# 重启AI-Sound后端服务脚本
Write-Host "🔄 重启AI-Sound后端服务（应用SongGeneration URL修复）..." -ForegroundColor Green

# 切换到项目目录
Set-Location "D:\AI-Sound"

# 重启后端服务
Write-Host "🔄 重启后端容器..." -ForegroundColor Yellow
docker-compose restart backend

# 等待服务启动
Write-Host "⏳ 等待后端服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "📊 检查后端服务状态..." -ForegroundColor Blue
docker-compose ps backend

# 显示后端日志
Write-Host "📄 显示后端启动日志..." -ForegroundColor Blue
docker-compose logs --tail=15 backend

# 测试后端健康检查
Write-Host "🔍 测试后端健康检查..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 10
    Write-Host "✅ 后端健康检查通过: $($response.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "❌ 后端健康检查失败: $($_.Exception.Message)" -ForegroundColor Red
}

# 测试音乐生成服务健康检查
Write-Host "🎵 测试音乐生成服务健康检查..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/music/health" -Method GET -TimeoutSec 10
    Write-Host "✅ 音乐生成服务健康检查通过: $($response.StatusCode)" -ForegroundColor Green
    $content = $response.Content | ConvertFrom-Json
    Write-Host "📊 服务状态: $($content.status)" -ForegroundColor Cyan
    Write-Host "🎵 引擎状态: $($content.engine_status)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ 音乐生成服务健康检查失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "✅ 后端重启完成！" -ForegroundColor Green
Write-Host "🔗 后端健康检查: http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "🎵 音乐生成健康检查: http://localhost:8000/api/v1/music/health" -ForegroundColor Cyan 