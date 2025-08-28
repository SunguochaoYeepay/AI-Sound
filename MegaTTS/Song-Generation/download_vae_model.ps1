# SongGeneration VAE模型下载脚本
Write-Host "🎵 下载SongGeneration VAE模型文件..." -ForegroundColor Green

# 创建VAE模型目录
$vaeDir = "ckpt/vae"
if (-not (Test-Path $vaeDir)) {
    New-Item -ItemType Directory -Path $vaeDir -Force | Out-Null
    Write-Host "✅ 创建VAE模型目录: $vaeDir" -ForegroundColor Green
}

Write-Host "📥 需要下载的VAE模型文件:" -ForegroundColor Yellow
Write-Host "   1. autoencoder_music_1320k.ckpt (约1.3GB)" -ForegroundColor White
Write-Host "   2. stable_audio_1920_vae.json (配置文件，已创建)" -ForegroundColor White

Write-Host ""
Write-Host "🔧 下载方式:" -ForegroundColor Cyan

Write-Host "方式1: 从HuggingFace官方仓库下载" -ForegroundColor Yellow
Write-Host "   访问: https://huggingface.co/tencent/SongGeneration/tree/main/ckpt/vae" -ForegroundColor White
Write-Host "   下载: autoencoder_music_1320k.ckpt" -ForegroundColor White
Write-Host "   保存到: $vaeDir\autoencoder_music_1320k.ckpt" -ForegroundColor White

Write-Host ""
Write-Host "方式2: 使用huggingface-hub命令行" -ForegroundColor Yellow
Write-Host "   pip install huggingface-hub" -ForegroundColor White
Write-Host "   huggingface-cli download tencent/SongGeneration ckpt/vae/autoencoder_music_1320k.ckpt --local-dir ./temp_download" -ForegroundColor White
Write-Host "   copy temp_download\ckpt\vae\autoencoder_music_1320k.ckpt $vaeDir\" -ForegroundColor White

Write-Host ""
Write-Host "方式3: 使用Python脚本下载" -ForegroundColor Yellow
Write-Host "   python -c 'from huggingface_hub import hf_hub_download; hf_hub_download(\"tencent/SongGeneration\", \"ckpt/vae/autoencoder_music_1320k.ckpt\", local_dir=\"$vaeDir\")'" -ForegroundColor White

Write-Host ""
Write-Host "📋 下载完成后，运行以下命令启动服务:" -ForegroundColor Green
Write-Host "   songgeneration_env\Scripts\activate" -ForegroundColor White
Write-Host "   `$env:PYTHONPATH = \"E:\AI-Sound\AI-Sound\MegaTTS\Song-Generation;`$env:PYTHONPATH\"" -ForegroundColor White
Write-Host "   python tools/gradio/app.py ckpt/songgeneration_base" -ForegroundColor White

Write-Host ""
Write-Host "⚠️  注意: VAE模型文件较大，请确保网络稳定" -ForegroundColor Red
Write-Host "   如果下载速度较慢，可以尝试使用代理或镜像源" -ForegroundColor Yellow
