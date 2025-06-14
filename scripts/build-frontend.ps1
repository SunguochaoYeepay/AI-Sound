# 前端构建脚本
Write-Host "🔨 开始构建前端..." -ForegroundColor Green

# 进入前端目录
Set-Location platform/frontend

# 检查依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 安装依赖..." -ForegroundColor Yellow
    npm install
}

# 构建
Write-Host "🚀 执行构建..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 前端构建完成!" -ForegroundColor Green
} else {
    Write-Host "❌ 前端构建失败!" -ForegroundColor Red
}

# 返回根目录
Set-Location ../.. 