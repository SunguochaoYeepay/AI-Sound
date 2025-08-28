# SongGeneration 简化版启动脚本
# 解决编码问题，使用简化版API服务器

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SongGeneration 简化版启动脚本" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "检查Python环境..." -ForegroundColor Green
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python环境检查失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Green
if (Test-Path "songgeneration_env\Scripts\Activate.ps1") {
    & "songgeneration_env\Scripts\Activate.ps1"
    Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green
} else {
    Write-Host "❌ 虚拟环境不存在" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查必要文件
Write-Host "检查必要文件..." -ForegroundColor Green
if (Test-Path "api_server_simple.py") {
    Write-Host "✅ 简化版API服务器文件存在" -ForegroundColor Green
} else {
    Write-Host "❌ 简化版API服务器文件不存在" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host ""
Write-Host "🚀 启动SongGeneration简化版API服务..." -ForegroundColor Yellow
Write-Host "📍 服务地址：http://127.0.0.1:7862" -ForegroundColor Cyan
Write-Host "📍 API文档：http://127.0.0.1:7862/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan

# 启动服务
try {
    python api_server_simple.py
} catch {
    Write-Host "❌ 服务启动失败: $($_.Exception.Message)" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "❌ 服务已停止" -ForegroundColor Red
    Read-Host "按任意键继续"
}
