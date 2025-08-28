# SongGeneration 环境测试脚本
Write-Host "🧪 测试SongGeneration环境..." -ForegroundColor Green

# 检查Python版本
Write-Host "🐍 检查Python版本..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python未安装或不在PATH中" -ForegroundColor Red
    exit 1
}

# 检查必要的Python包
Write-Host "📦 检查Python依赖..." -ForegroundColor Cyan
$requiredPackages = @("torch", "torchaudio", "fastapi", "uvicorn", "omegaconf", "gradio")
foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" 2>$null
        Write-Host "✅ $package 已安装" -ForegroundColor Green
    } catch {
        Write-Host "❌ $package 未安装" -ForegroundColor Red
    }
}

# 检查CUDA
Write-Host "🎮 检查CUDA..." -ForegroundColor Cyan
try {
    python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>$null
} catch {
    Write-Host "⚠️  CUDA检查失败" -ForegroundColor Yellow
}

# 检查项目文件
Write-Host "📁 检查项目文件..." -ForegroundColor Cyan
$requiredFiles = @("api_server.py", "requirements.txt", "codeclm/", "tools/", "third_party/")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file 存在" -ForegroundColor Green
    } else {
        Write-Host "❌ $file 不存在" -ForegroundColor Red
    }
}

# 检查模型文件
Write-Host "🤖 检查模型文件..." -ForegroundColor Cyan
$modelPath = "ckpt/songgeneration_base"
if (Test-Path $modelPath) {
    Write-Host "✅ 模型目录存在: $modelPath" -ForegroundColor Green
    $modelFiles = @("config.yaml", "model.pt", "prompt.pt")
    foreach ($file in $modelFiles) {
        $fullPath = Join-Path $modelPath $file
        if (Test-Path $fullPath) {
            $size = (Get-Item $fullPath).Length / 1GB
            Write-Host "✅ $file 存在 (${size:F2}GB)" -ForegroundColor Green
        } else {
            Write-Host "❌ $file 不存在" -ForegroundColor Red
        }
    }
} else {
    Write-Host "❌ 模型目录不存在: $modelPath" -ForegroundColor Red
    Write-Host "💡 请运行 .\download_model.ps1 下载模型文件" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 环境测试完成！" -ForegroundColor Green
