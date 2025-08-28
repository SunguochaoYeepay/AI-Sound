# SongGeneration 完整模型下载脚本
Write-Host "🎵 下载SongGeneration完整模型包..." -ForegroundColor Green

Write-Host "📥 推荐下载方式：使用官方完整模型包" -ForegroundColor Yellow
Write-Host "   这样可以确保所有文件都是兼容的" -ForegroundColor Yellow

Write-Host ""
Write-Host "🔧 方式1: 使用git-lfs下载完整仓库（推荐）" -ForegroundColor Cyan
Write-Host "   1. 安装git-lfs: https://git-lfs.com/" -ForegroundColor White
Write-Host "   2. 运行命令:" -ForegroundColor White
Write-Host "      git lfs install" -ForegroundColor White
Write-Host "      git clone https://huggingface.co/tencent/SongGeneration" -ForegroundColor White
Write-Host "      copy SongGeneration\ckpt\* ckpt\" -ForegroundColor White

Write-Host ""
Write-Host "🔧 方式2: 使用huggingface-hub下载完整模型" -ForegroundColor Cyan
Write-Host "   1. 安装: pip install huggingface-hub" -ForegroundColor White
Write-Host "   2. 运行: huggingface-cli download tencent/SongGeneration --local-dir ./temp_download" -ForegroundColor White
Write-Host "   3. 复制: copy temp_download\ckpt\* ckpt\" -ForegroundColor White

Write-Host ""
Write-Host "🔧 方式3: 手动下载关键文件" -ForegroundColor Cyan
Write-Host "   访问: https://huggingface.co/tencent/SongGeneration/tree/main/ckpt" -ForegroundColor White
Write-Host "   下载以下目录到 ckpt 文件夹:" -ForegroundColor White
Write-Host "      - songgeneration_base/ (主模型)" -ForegroundColor White
Write-Host "      - vae/ (VAE模型)" -ForegroundColor White
Write-Host "      - model_1rvq/ (音频编码器)" -ForegroundColor White
Write-Host "      - model_septoken/ (分离编码器)" -ForegroundColor White

Write-Host ""
Write-Host "📋 下载完成后，运行以下命令启动服务:" -ForegroundColor Green
Write-Host "   songgeneration_env\Scripts\activate" -ForegroundColor White
Write-Host "   `$env:PYTHONPATH = \"E:\AI-Sound\AI-Sound\MegaTTS\Song-Generation;`$env:PYTHONPATH\"" -ForegroundColor White
Write-Host "   python tools/gradio/app.py ckpt/songgeneration_base" -ForegroundColor White

Write-Host ""
Write-Host "⚠️  注意: 完整模型包约15GB，请确保网络稳定和足够存储空间" -ForegroundColor Red
Write-Host "   建议使用方式1或方式2，确保文件完整性" -ForegroundColor Yellow
