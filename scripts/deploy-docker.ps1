#!/usr/bin/env pwsh
# AI-Sound Docker部署脚本

Write-Host "🚀 开始AI-Sound Docker部署..." -ForegroundColor Green

# 检查Docker是否运行
Write-Host "📋 检查Docker状态..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker运行正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker未运行，请启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 停止现有服务
Write-Host "🛑 停止现有服务..." -ForegroundColor Yellow
docker compose down 2>$null

# 构建前端
Write-Host "🔨 构建前端应用..." -ForegroundColor Yellow
Set-Location platform/frontend
if (Test-Path "node_modules") {
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ 前端构建失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ 前端构建完成" -ForegroundColor Green
} else {
    Write-Host "⚠️ 前端依赖未安装，跳过构建" -ForegroundColor Yellow
}
Set-Location ../..

# 构建后端镜像
Write-Host "🔨 构建后端镜像..." -ForegroundColor Yellow
docker build -f docker/backend/Dockerfile -t ai-sound-backend:latest .
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 后端镜像构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 后端镜像构建完成" -ForegroundColor Green

# 检查MegaTTS3镜像
Write-Host "📋 检查MegaTTS3镜像..." -ForegroundColor Yellow
$megatts3Image = docker images -q megatts3:latest
if (-not $megatts3Image) {
    Write-Host "⚠️ MegaTTS3镜像不存在，请先构建MegaTTS3镜像" -ForegroundColor Yellow
    Write-Host "   可以运行: docker build -t megatts3:latest MegaTTS/MegaTTS3/" -ForegroundColor Cyan
} else {
    Write-Host "✅ MegaTTS3镜像存在" -ForegroundColor Green
}

# 创建必要的目录
Write-Host "📁 创建数据目录..." -ForegroundColor Yellow
$directories = @(
    "data/audio",
    "data/uploads", 
    "data/voice_profiles",
    "data/projects",
    "data/logs/nginx",
    "data/cache"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ 创建目录: $dir" -ForegroundColor Green
    }
}

# 启动服务
Write-Host "🚀 启动Docker服务..." -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 服务启动失败" -ForegroundColor Red
    exit 1
}

# 等待服务启动
Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 检查服务状态
Write-Host "📋 检查服务状态..." -ForegroundColor Yellow
docker compose ps

# 显示访问信息
Write-Host ""
Write-Host "🎉 部署完成！" -ForegroundColor Green
Write-Host "📱 前端访问地址: http://localhost:3001" -ForegroundColor Cyan
Write-Host "🔧 后端API地址: http://localhost:3001/api" -ForegroundColor Cyan
Write-Host "🎵 TTS服务地址: http://localhost:7929" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 查看日志命令:" -ForegroundColor Yellow
Write-Host "   docker compose logs -f backend" -ForegroundColor Gray
Write-Host "   docker compose logs -f nginx" -ForegroundColor Gray
Write-Host "   docker compose logs -f megatts3" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 停止服务命令:" -ForegroundColor Yellow
Write-Host "   docker compose down" -ForegroundColor Gray 