# 重新构建SongGeneration服务（使用软连接挂载模型）
Write-Host "🎵 重新构建SongGeneration服务（软连接模型方案）..." -ForegroundColor Green

# 切换到项目目录
Set-Location "D:\AI-Sound"

# 检查模型目录是否存在
$modelPath = "SongGeneration-Official-Demo\SongGeneration\ckpt"
if (Test-Path $modelPath) {
    $modelSize = (Get-ChildItem $modelPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "✅ 发现模型目录: $modelPath (约 $([math]::Round($modelSize, 1)) GB)" -ForegroundColor Green
} else {
    Write-Host "❌ 模型目录不存在: $modelPath" -ForegroundColor Red
    Write-Host "请检查模型目录路径是否正确" -ForegroundColor Yellow
    exit 1
}

# 停止并删除现有容器
Write-Host "🛑 停止现有SongGeneration容器..." -ForegroundColor Yellow
docker stop ai-sound-songgeneration 2>$null
docker rm ai-sound-songgeneration 2>$null

# 删除旧镜像
Write-Host "🗑️ 删除旧镜像..." -ForegroundColor Yellow
docker rmi ai-sound_songgeneration 2>$null

# 重新构建镜像
Write-Host "🔨 重新构建SongGeneration镜像（轻量级，不包含模型）..." -ForegroundColor Green
docker-compose build songgeneration

# 启动服务（使用volume挂载模型）
Write-Host "🚀 启动SongGeneration服务（volume挂载模型）..." -ForegroundColor Green
docker-compose up -d songgeneration

# 等待启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "📊 检查服务状态..." -ForegroundColor Blue
docker-compose ps songgeneration

# 显示详细日志
Write-Host "📄 显示启动日志..." -ForegroundColor Blue
docker-compose logs --tail=30 songgeneration

# 测试模型检测
Write-Host "🧪 测试模型检测..." -ForegroundColor Blue
Start-Sleep -Seconds 5
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081/test" -Method GET -TimeoutSec 10
    $content = $response.Content | ConvertFrom-Json
    Write-Host "✅ SongGeneration服务响应正常" -ForegroundColor Green
    Write-Host "📍 当前目录: $($content.paths.current)" -ForegroundColor Cyan
    Write-Host "📁 工作空间存在: $($content.paths.workspace_exists)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ 服务还在启动中..." -ForegroundColor Yellow
}

Write-Host "✅ 重新构建完成！" -ForegroundColor Green
Write-Host "💡 优势:" -ForegroundColor Cyan
Write-Host "   - 🚀 构建速度快（无需复制70GB模型）" -ForegroundColor White
Write-Host "   - 💾 节省磁盘空间（软连接挂载）" -ForegroundColor White
Write-Host "   - 🔄 模型更新实时同步" -ForegroundColor White
Write-Host "   - 🎯 完整模型文件可用" -ForegroundColor White
Write-Host ""
Write-Host "🔗 测试链接:" -ForegroundColor Cyan
Write-Host "   健康检查: http://localhost:8081/health" -ForegroundColor White
Write-Host "   测试接口: http://localhost:8081/test" -ForegroundColor White
Write-Host "   API文档: http://localhost:8081/docs" -ForegroundColor White 