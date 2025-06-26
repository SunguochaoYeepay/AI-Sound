# 重新构建SongGeneration服务（带Gradio界面）
Write-Host "🎨 重新构建SongGeneration服务（API + Gradio界面）..." -ForegroundColor Green

# 切换到项目目录
Set-Location "D:\AI-Sound"

# 检查模型目录
$modelPath = "SongGeneration-Official-Demo\SongGeneration\ckpt"
if (Test-Path $modelPath) {
    $modelSize = (Get-ChildItem $modelPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "✅ 模型目录: $modelPath (约 $([math]::Round($modelSize, 1)) GB)" -ForegroundColor Green
} else {
    Write-Host "❌ 模型目录不存在: $modelPath" -ForegroundColor Red
    exit 1
}

# 检查官方Gradio工具
$gradioPath = "SongGeneration-Official-Demo\SongGeneration\tools\gradio\app.py"
if (Test-Path $gradioPath) {
    Write-Host "✅ 官方Gradio界面: $gradioPath" -ForegroundColor Green
} else {
    Write-Host "❌ 官方Gradio界面不存在: $gradioPath" -ForegroundColor Red
    exit 1
}

# 停止现有容器
Write-Host "🛑 停止现有容器..." -ForegroundColor Yellow
docker stop ai-sound-songgeneration 2>$null
docker rm ai-sound-songgeneration 2>$null

# 删除旧镜像
Write-Host "🗑️ 删除旧镜像..." -ForegroundColor Yellow
docker rmi ai-sound_songgeneration 2>$null

# 重新构建镜像
Write-Host "🔨 重新构建镜像（包含Gradio界面）..." -ForegroundColor Green
docker-compose build songgeneration

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 镜像构建失败" -ForegroundColor Red
    exit 1
}

# 启动服务
Write-Host "🚀 启动双服务模式..." -ForegroundColor Green
docker-compose up -d songgeneration

# 等待启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 检查服务状态
Write-Host "📊 检查服务状态..." -ForegroundColor Blue
docker-compose ps songgeneration

# 显示启动日志
Write-Host "📄 显示启动日志..." -ForegroundColor Blue
docker-compose logs --tail=25 songgeneration

# 测试API
Write-Host "🧪 测试API服务..." -ForegroundColor Blue
Start-Sleep -Seconds 5
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081/test" -Method GET -TimeoutSec 15
    $content = $response.Content | ConvertFrom-Json
    Write-Host "✅ API服务正常" -ForegroundColor Green
    Write-Host "📍 运行模式: $($content.mode)" -ForegroundColor Cyan
    Write-Host "🎨 Gradio服务: $($content.services.gradio)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️ API服务测试失败: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 测试Gradio界面
Write-Host "🎨 测试Gradio界面..." -ForegroundColor Blue
try {
    $response = Invoke-WebRequest -Uri "http://localhost:7862" -Method GET -TimeoutSec 15
    Write-Host "✅ Gradio界面可访问" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Gradio界面测试失败: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "✅ 双服务启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 服务地址:" -ForegroundColor Cyan
Write-Host "   🎨 Gradio Web界面: http://localhost:7862" -ForegroundColor White
Write-Host "   📡 API服务端点: http://localhost:8081" -ForegroundColor White
Write-Host "   🔍 API健康检查: http://localhost:8081/health" -ForegroundColor White
Write-Host "   🧪 API测试接口: http://localhost:8081/test" -ForegroundColor White
Write-Host "   📋 API文档: http://localhost:8081/docs" -ForegroundColor White
Write-Host ""
Write-Host "💡 使用说明:" -ForegroundColor Yellow
Write-Host "   - Web界面: 直接在浏览器中操作，支持歌词输入、风格选择" -ForegroundColor White
Write-Host "   - API接口: 可以通过HTTP请求调用音乐生成功能" -ForegroundColor White
Write-Host "   - 模型文件: 通过volume挂载，无需重复复制" -ForegroundColor White 