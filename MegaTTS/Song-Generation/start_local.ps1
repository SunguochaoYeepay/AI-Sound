# SongGeneration 本地启动脚本
param(
    [string]$Port = "7862"
)

Write-Host "🎵 启动本地SongGeneration服务..." -ForegroundColor Green
Write-Host "📁 工作目录: $(Get-Location)" -ForegroundColor Cyan
Write-Host "🌐 端口: $Port" -ForegroundColor Cyan

# 检查必要的目录
$ckptPath = "ckpt/songgeneration_base"
if (-not (Test-Path $ckptPath)) {
    Write-Host "❌ 模型文件不存在: $ckptPath" -ForegroundColor Red
    Write-Host "💡 请下载模型文件到: $ckptPath" -ForegroundColor Yellow
    Write-Host "   下载地址: https://huggingface.co/tencent/SongGeneration/tree/main/ckpt/songgeneration_base" -ForegroundColor Yellow
    exit 1
}

# 创建必要的目录
$directories = @("output", "temp", "output/api_generated")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✅ 创建目录: $dir" -ForegroundColor Green
    }
}

# 设置环境变量
$env:USER = "root"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:TRANSFORMERS_CACHE = "$(Get-Location)/third_party/hub"
$env:NCCL_HOME = "/usr/local/tccl"
$env:PYTHONPATH = "$(Get-Location)/codeclm/tokenizer/;$(Get-Location);$(Get-Location)/codeclm/tokenizer/Flow1dVAE/;$(Get-Location)/codeclm/tokenizer/;$env:PYTHONPATH"

Write-Host "🚀 启动API服务器..." -ForegroundColor Green
Write-Host "📁 模型路径: $ckptPath" -ForegroundColor Cyan
Write-Host "🌐 服务地址: http://localhost:$Port" -ForegroundColor Cyan

# 启动API服务器
try {
    python api_server.py $ckptPath $Port
} catch {
    Write-Host "❌ 启动失败: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
