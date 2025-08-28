# TangoFlux 环境音生成服务启动脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   TangoFlux 环境音生成服务启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查虚拟环境是否存在
$envPath = "MegaTTS\TangoFlux\tangoflux_env"
if (-not (Test-Path $envPath)) {
    Write-Host "❌ 错误：虚拟环境不存在！" -ForegroundColor Red
    Write-Host "请先创建虚拟环境：python -m venv MegaTTS\TangoFlux\tangoflux_env" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

# 切换到TangoFlux目录
Set-Location "MegaTTS\TangoFlux"

# 激活虚拟环境
Write-Host "🔄 激活虚拟环境..." -ForegroundColor Green
& "$envPath\Scripts\Activate.ps1"

# 检查激活是否成功
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 虚拟环境激活失败！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查Python和依赖
Write-Host "🔍 检查Python环境..." -ForegroundColor Green
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python未找到！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查必要文件
if (-not (Test-Path "tangoflux_api_server.py")) {
    Write-Host "❌ 找不到 tangoflux_api_server.py！" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 启动服务
Write-Host ""
Write-Host "🚀 启动TangoFlux API服务..." -ForegroundColor Green
Write-Host "📍 服务地址：http://127.0.0.1:7930" -ForegroundColor Yellow
Write-Host "📍 API文档：http://127.0.0.1:7930/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 启动服务
try {
    python tangoflux_api_server.py
} catch {
    Write-Host ""
    Write-Host "❌ 服务启动失败：$($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "❌ 服务已停止" -ForegroundColor Red
Read-Host "按回车键退出"
