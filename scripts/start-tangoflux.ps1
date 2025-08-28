# TangoFlux服务启动脚本
# 设置UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 启动TangoFlux环境音生成服务..." -ForegroundColor Green

# 检查虚拟环境是否存在
$envPath = "MegaTTS\TangoFlux\tangoflux_env"
if (-not (Test-Path $envPath)) {
    Write-Host "❌ TangoFlux虚拟环境不存在，正在创建..." -ForegroundColor Red
    Set-Location "MegaTTS\TangoFlux"
    python -m venv tangoflux_env
    Set-Location ..\..
}

# 激活虚拟环境
Write-Host "📍 激活TangoFlux虚拟环境..." -ForegroundColor Yellow
& "MegaTTS\TangoFlux\tangoflux_env\Scripts\Activate.ps1"

# 进入TangoFlux目录
Set-Location "MegaTTS\TangoFlux"

# 检查依赖是否安装
if (-not (Test-Path "tangoflux_env\Lib\site-packages\torch")) {
    Write-Host "📦 安装TangoFlux依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# 启动服务
Write-Host "🎯 启动TangoFlux API服务器..." -ForegroundColor Cyan
Write-Host "🌐 服务地址: http://localhost:7930" -ForegroundColor Blue
Write-Host "📚 API文档: http://localhost:7930/docs" -ForegroundColor Blue
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow

python tangoflux_api_server.py
