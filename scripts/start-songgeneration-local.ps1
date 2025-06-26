# 启动本地虚拟环境的SongGeneration服务
param(
    [string]$Port = "7863"
)

# 设置工作目录
$SongGenDir = "D:\AI-Sound\MegaTTS\SongGeneration"
$VenvPath = "$SongGenDir\songgen_env"

Write-Host "🎵 启动本地SongGeneration服务..." -ForegroundColor Green
Write-Host "📁 工作目录: $SongGenDir" -ForegroundColor Cyan
Write-Host "🐍 虚拟环境: $VenvPath" -ForegroundColor Cyan
Write-Host "🌐 端口: $Port" -ForegroundColor Cyan

# 检查虚拟环境是否存在
if (-not (Test-Path "$VenvPath\Scripts\activate.ps1")) {
    Write-Host "❌ 虚拟环境不存在: $VenvPath" -ForegroundColor Red
    Write-Host "💡 请先创建虚拟环境：" -ForegroundColor Yellow
    Write-Host "   cd $SongGenDir" -ForegroundColor Yellow
    Write-Host "   python -m venv songgen_env" -ForegroundColor Yellow
    Write-Host "   .\songgen_env\Scripts\activate" -ForegroundColor Yellow
    Write-Host "   pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 检查server.py是否存在
if (-not (Test-Path "$SongGenDir\server.py")) {
    Write-Host "❌ SongGeneration服务文件不存在: $SongGenDir\server.py" -ForegroundColor Red
    exit 1
}

try {
    # 切换到SongGeneration目录
    Set-Location $SongGenDir
    
    # 激活虚拟环境并启动服务
    & "$VenvPath\Scripts\activate.ps1"
    
    # 设置环境变量
    $env:SERVER_HOST = "0.0.0.0"
    $env:SERVER_PORT = $Port
    $env:PYTHONPATH = $SongGenDir
    
    Write-Host "🚀 启动SongGeneration服务..." -ForegroundColor Green
    
    # 启动服务
    & "$VenvPath\Scripts\python.exe" server.py
    
} catch {
    Write-Host "❌ 启动失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # 返回原目录
    Set-Location "D:\AI-Sound"
} 