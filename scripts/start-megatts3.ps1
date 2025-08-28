# MegaTTS3服务启动脚本
# 设置UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🎤 启动MegaTTS3语音合成服务..." -ForegroundColor Green

# 检查虚拟环境是否存在
$envPath = "MegaTTS\espnet\espnet_env"
if (-not (Test-Path $envPath)) {
    Write-Host "❌ MegaTTS3虚拟环境不存在，正在创建..." -ForegroundColor Red
    Set-Location "MegaTTS\espnet"
    python -m venv espnet_env
    Set-Location ..\..
}

# 激活虚拟环境
Write-Host "📍 激活MegaTTS3虚拟环境..." -ForegroundColor Yellow
& "MegaTTS\espnet\espnet_env\Scripts\Activate.ps1"

# 进入espnet目录
Set-Location "MegaTTS\espnet"

# 检查依赖是否安装
if (-not (Test-Path "espnet_env\Lib\site-packages\flask")) {
    Write-Host "📦 安装MegaTTS3依赖..." -ForegroundColor Yellow
    Write-Host "⚠️  注意：某些依赖可能需要编译，如果安装失败请手动处理" -ForegroundColor Red
    pip install -r requirements.txt
}

# 启动服务
Write-Host "🎯 启动MegaTTS3 API服务器..." -ForegroundColor Cyan
Write-Host "🌐 服务地址: http://localhost:7929" -ForegroundColor Blue
Write-Host "📚 API文档: http://localhost:7929/docs" -ForegroundColor Blue
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow

python megatts3_api_server.py
