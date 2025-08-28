# AI-Sound后端启动脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI-Sound后端启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到后端目录
Write-Host "📁 切换到后端目录..." -ForegroundColor Green
Set-Location "platform\backend"

# 激活虚拟环境
Write-Host "🔧 激活虚拟环境..." -ForegroundColor Green
& "..\..\.venv\Scripts\Activate.ps1"

# 设置环境变量
Write-Host "🔧 设置环境变量..." -ForegroundColor Green
# $env:DATABASE_URL = "mysql+pymysql://ai_sound_user:ai_sound_password@localhost:3306/ai_sound" # MySQL配置
$env:DEBUG = "true"
$env:LOCAL_DEV = "true"
$env:ECHO_SQL = "false"

Write-Host "✅ 数据库URL: $env:DATABASE_URL" -ForegroundColor Green
Write-Host "✅ 调试模式: $env:DEBUG" -ForegroundColor Green
Write-Host "✅ 本地开发: $env:LOCAL_DEV" -ForegroundColor Green

# 创建数据目录
Write-Host "📁 创建数据目录..." -ForegroundColor Green
if (!(Test-Path ".\data")) {
    New-Item -ItemType Directory -Path ".\data" -Force
    Write-Host "✅ 数据目录创建成功" -ForegroundColor Green
}

# 启动后端
Write-Host "🚀 启动后端服务..." -ForegroundColor Green
Write-Host "📍 服务地址: http://localhost:8001" -ForegroundColor Yellow
Write-Host "📖 API文档: http://localhost:8001/docs" -ForegroundColor Yellow
Write-Host ""

python main.py
