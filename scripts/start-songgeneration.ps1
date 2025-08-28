# SongGeneration服务启动脚本
# 设置UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🎵 启动SongGeneration音乐生成服务..." -ForegroundColor Green

# 检查虚拟环境是否存在
$envPath = "MegaTTS\Song-Generation\songgeneration_env"
if (-not (Test-Path $envPath)) {
    Write-Host "❌ SongGeneration虚拟环境不存在，正在创建..." -ForegroundColor Red
    Set-Location "MegaTTS\Song-Generation"
    python -m venv songgeneration_env
    Set-Location ..\..
}

# 激活虚拟环境
Write-Host "📍 激活SongGeneration虚拟环境..." -ForegroundColor Yellow
& "MegaTTS\Song-Generation\songgeneration_env\Scripts\Activate.ps1"

# 进入SongGeneration目录
Set-Location "MegaTTS\Song-Generation"

# 检查依赖是否安装
if (-not (Test-Path "songgeneration_env\Lib\site-packages\gradio")) {
    Write-Host "📦 安装SongGeneration依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# 启动服务
Write-Host "🎯 启动SongGeneration API服务器..." -ForegroundColor Cyan
Write-Host "🌐 服务地址: http://localhost:7862" -ForegroundColor Blue
Write-Host "📚 API文档: http://localhost:7862/docs" -ForegroundColor Blue
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow

python api_server.py
