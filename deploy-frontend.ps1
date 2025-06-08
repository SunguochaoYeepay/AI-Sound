#!/usr/bin/env pwsh
# 前端自动部署脚本

Write-Host "🚀 开始前端部署..." -ForegroundColor Green

# 1. 进入前端目录并构建
Write-Host "📦 构建前端项目..." -ForegroundColor Yellow
Set-Location "platform/frontend"
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 前端构建失败！" -ForegroundColor Red
    exit 1
}

# 2. 回到项目根目录
Set-Location "../.."

# 3. 清空nginx-dist目录
Write-Host "🧹 清理旧文件..." -ForegroundColor Yellow
if (Test-Path "nginx-dist") {
    Remove-Item -Path "nginx-dist/*" -Recurse -Force
}

# 4. 复制新文件到nginx-dist
Write-Host "📋 复制新文件..." -ForegroundColor Yellow
Copy-Item -Path "platform/frontend/dist/*" -Destination "nginx-dist/" -Recurse -Force

# 5. 重启nginx
Write-Host "🔄 重启nginx服务..." -ForegroundColor Yellow
docker-compose restart nginx

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 前端部署成功！" -ForegroundColor Green
    Write-Host "🌐 访问地址: http://localhost:3001" -ForegroundColor Cyan
} else {
    Write-Host "❌ nginx重启失败！" -ForegroundColor Red
    exit 1
} 