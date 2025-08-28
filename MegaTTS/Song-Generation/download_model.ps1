# SongGeneration 模型下载脚本
Write-Host "🎵 下载SongGeneration模型文件..." -ForegroundColor Green

# 创建模型目录
$modelDir = "ckpt/songgeneration_base"
if (-not (Test-Path $modelDir)) {
    New-Item -ItemType Directory -Path $modelDir -Force | Out-Null
    Write-Host "✅ 创建模型目录: $modelDir" -ForegroundColor Green
}

Write-Host "📥 开始下载模型文件..." -ForegroundColor Yellow
Write-Host "⚠️  模型文件大小约11GB，请确保网络稳定" -ForegroundColor Red

# 使用git-lfs下载（推荐方式）
Write-Host "🔧 方式1: 使用git-lfs下载（推荐）" -ForegroundColor Cyan
Write-Host "   1. 安装git-lfs: https://git-lfs.com/" -ForegroundColor Yellow
Write-Host "   2. 运行命令:" -ForegroundColor Yellow
Write-Host "      git lfs install" -ForegroundColor White
Write-Host "      git clone https://huggingface.co/tencent/SongGeneration" -ForegroundColor White
Write-Host "      copy SongGeneration\ckpt\songgeneration_base\* $modelDir\" -ForegroundColor White

Write-Host ""
Write-Host "🔧 方式2: 手动下载" -ForegroundColor Cyan
Write-Host "   1. 访问: https://huggingface.co/tencent/SongGeneration/tree/main/ckpt/songgeneration_base" -ForegroundColor Yellow
Write-Host "   2. 下载以下文件到 $modelDir 目录:" -ForegroundColor Yellow
Write-Host "      - config.yaml" -ForegroundColor White
Write-Host "      - model.pt (约11GB)" -ForegroundColor White
Write-Host "      - prompt.pt" -ForegroundColor White

Write-Host ""
Write-Host "🔧 方式3: 使用huggingface-hub" -ForegroundColor Cyan
Write-Host "   1. 安装: pip install huggingface-hub" -ForegroundColor Yellow
Write-Host "   2. 运行: python -c 'from huggingface_hub import snapshot_download; snapshot_download(\"tencent/SongGeneration\", local_dir=\"./temp_download\", include=[\"ckpt/songgeneration_base/*\"])'" -ForegroundColor White

Write-Host ""
Write-Host "📋 下载完成后，运行以下命令启动服务:" -ForegroundColor Green
Write-Host "   .\start_local.ps1" -ForegroundColor White
