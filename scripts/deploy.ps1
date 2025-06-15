# AI-Sound Docker部署脚本 (Windows PowerShell版本)
# 支持Windows宿主机Ollama服务集成

param(
    [switch]$SkipBuild,
    [switch]$SkipFrontend,
    [switch]$Help
)

# 错误处理
$ErrorActionPreference = "Stop"

# 颜色函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    switch ($Color) {
        "Red" { Write-Host $Message -ForegroundColor Red }
        "Green" { Write-Host $Message -ForegroundColor Green }
        "Yellow" { Write-Host $Message -ForegroundColor Yellow }
        "Blue" { Write-Host $Message -ForegroundColor Blue }
        default { Write-Host $Message }
    }
}

function Log-Info {
    param([string]$Message)
    Write-ColorOutput "[INFO] $Message" "Blue"
}

function Log-Success {
    param([string]$Message)
    Write-ColorOutput "[SUCCESS] $Message" "Green"
}

function Log-Warning {
    param([string]$Message)
    Write-ColorOutput "[WARNING] $Message" "Yellow"
}

function Log-Error {
    param([string]$Message)
    Write-ColorOutput "[ERROR] $Message" "Red"
}

# 显示帮助信息
function Show-Help {
    Write-Host "AI-Sound Docker部署脚本"
    Write-Host "用法: .\deploy.ps1 [选项]"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  -SkipBuild      跳过Docker镜像构建"
    Write-Host "  -SkipFrontend   跳过前端构建"
    Write-Host "  -Help           显示帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\deploy.ps1                    # 完整部署"
    Write-Host "  .\deploy.ps1 -SkipFrontend      # 跳过前端构建"
    Write-Host "  .\deploy.ps1 -SkipBuild         # 跳过镜像构建"
}

# 检查必要工具
function Test-Requirements {
    Log-Info "检查部署环境..."
    
    # 检查Docker
    try {
        $dockerVersion = docker --version
        Log-Success "Docker已安装: $dockerVersion"
    }
    catch {
        Log-Error "Docker未安装，请先安装Docker Desktop"
        exit 1
    }
    
    # 检查Docker Compose
    try {
        $composeVersion = docker-compose --version
        Log-Success "Docker Compose已安装: $composeVersion"
    }
    catch {
        Log-Error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    }
    
    # 检查Node.js
    try {
        $nodeVersion = node --version
        Log-Success "Node.js已安装: $nodeVersion"
    }
    catch {
        Log-Error "Node.js未安装，请先安装Node.js 18+"
        exit 1
    }
    
    # 检查npm
    try {
        $npmVersion = npm --version
        Log-Success "npm已安装: $npmVersion"
    }
    catch {
        Log-Error "npm未安装，请先安装npm"
        exit 1
    }
    
    Log-Success "环境检查通过"
}

# 检查Ollama服务
function Test-Ollama {
    Log-Info "检查Ollama服务..."
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
        Log-Success "Ollama服务运行正常"
        
        # 检查模型
        $hasGemma = $response.models | Where-Object { $_.name -like "*gemma3:27b*" }
        if ($hasGemma) {
            Log-Success "Gemma3:27b模型已安装"
        } else {
            Log-Warning "Gemma3:27b模型未安装，请运行: ollama pull gemma3:27b"
        }
    }
    catch {
        Log-Warning "Ollama服务未运行，请确保Ollama在Windows上正常启动"
        Log-Info "启动命令: ollama serve"
    }
}

# 创建必要目录
function New-Directories {
    Log-Info "创建必要目录..."
    
    $directories = @(
        "data\audio",
        "data\database", 
        "data\logs",
        "data\logs\nginx",
        "data\uploads",
        "data\voice_profiles",
        "data\cache",
        "data\config",
        "data\backups",
        "data\temp",
        "data\tts",
        "nginx-dist"
    )
    
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Log-Success "目录创建完成"
}

# 构建前端
function Build-Frontend {
    Log-Info "构建前端应用..."
    
    Push-Location "platform\frontend"
    
    try {
        # 安装依赖
        Log-Info "安装前端依赖..."
        npm install
        
        # 构建生产版本
        Log-Info "构建生产版本..."
        npm run build
        
        # 复制构建产物
        Log-Info "复制构建产物..."
        if (Test-Path "dist") {
            Copy-Item -Path "dist\*" -Destination "..\..\nginx-dist\" -Recurse -Force
        } else {
            throw "构建产物目录不存在"
        }
        
        Log-Success "前端构建完成"
    }
    catch {
        Log-Error "前端构建失败: $($_.Exception.Message)"
        exit 1
    }
    finally {
        Pop-Location
    }
}

# 构建Docker镜像
function Build-Images {
    Log-Info "构建Docker镜像..."
    
    try {
        # 构建后端镜像
        Log-Info "构建后端镜像..."
        docker build -t ai-sound-backend:latest -f docker/backend/Dockerfile .
        
        Log-Success "Docker镜像构建完成"
    }
    catch {
        Log-Error "Docker镜像构建失败: $($_.Exception.Message)"
        exit 1
    }
}

# 启动服务
function Start-Services {
    Log-Info "启动Docker服务..."
    
    try {
        # 停止现有服务
        docker-compose down
        
        # 启动服务
        docker-compose up -d
        
        Log-Success "Docker服务启动完成"
    }
    catch {
        Log-Error "Docker服务启动失败: $($_.Exception.Message)"
        exit 1
    }
}

# 等待服务就绪
function Wait-ForServices {
    Log-Info "等待服务启动..."
    
    # 等待数据库
    Log-Info "等待数据库启动..."
    $timeout = 60
    while ($timeout -gt 0) {
        try {
            $result = docker-compose exec -T database pg_isready -U ai_sound_user -d ai_sound 2>$null
            if ($LASTEXITCODE -eq 0) {
                break
            }
        }
        catch { }
        
        Start-Sleep -Seconds 2
        $timeout -= 2
    }
    
    if ($timeout -le 0) {
        Log-Error "数据库启动超时"
        exit 1
    }
    Log-Success "数据库启动完成"
    
    # 等待后端
    Log-Info "等待后端服务启动..."
    $timeout = 60
    while ($timeout -gt 0) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:3001/api/health" -Method Get -TimeoutSec 2
            break
        }
        catch {
            Start-Sleep -Seconds 2
            $timeout -= 2
        }
    }
    
    if ($timeout -le 0) {
        Log-Error "后端服务启动超时"
        exit 1
    }
    Log-Success "后端服务启动完成"
    
    # 等待前端
    Log-Info "等待前端服务启动..."
    $timeout = 30
    while ($timeout -gt 0) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3001" -Method Get -TimeoutSec 2
            break
        }
        catch {
            Start-Sleep -Seconds 2
            $timeout -= 2
        }
    }
    
    if ($timeout -le 0) {
        Log-Error "前端服务启动超时"
        exit 1
    }
    Log-Success "前端服务启动完成"
}

# 显示部署信息
function Show-DeploymentInfo {
    Log-Success "🎉 AI-Sound部署完成！"
    Write-Host ""
    Write-Host "📋 服务信息:"
    Write-Host "  🌐 前端界面: http://localhost:3001"
    Write-Host "  🔧 API文档:  http://localhost:3001/docs"
    Write-Host "  📊 健康检查: http://localhost:3001/api/health"
    Write-Host ""
    Write-Host "🐳 Docker服务状态:"
    docker-compose ps
    Write-Host ""
    Write-Host "📝 日志查看:"
    Write-Host "  docker-compose logs -f backend"
    Write-Host "  docker-compose logs -f nginx"
    Write-Host ""
    Write-Host "🔧 管理命令:"
    Write-Host "  停止服务: docker-compose down"
    Write-Host "  重启服务: docker-compose restart"
    Write-Host "  查看状态: docker-compose ps"
    Write-Host ""
    
    # 检查Ollama连接
    try {
        Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5 | Out-Null
        Log-Success "✅ Ollama服务连接正常"
    }
    catch {
        Log-Warning "⚠️  Ollama服务连接失败，请检查Windows上的Ollama服务"
    }
}

# 主函数
function Main {
    Write-Host "🚀 AI-Sound Docker部署脚本"
    Write-Host "支持Windows宿主机Ollama服务集成"
    Write-Host ""
    
    if ($Help) {
        Show-Help
        return
    }
    
    try {
        # 执行部署步骤
        Test-Requirements
        Test-Ollama
        New-Directories
        
        if (!$SkipFrontend) {
            Build-Frontend
        } else {
            Log-Warning "跳过前端构建"
        }
        
        if (!$SkipBuild) {
            Build-Images
        } else {
            Log-Warning "跳过Docker镜像构建"
        }
        
        Start-Services
        Wait-ForServices
        Show-DeploymentInfo
    }
    catch {
        Log-Error "部署过程中发生错误: $($_.Exception.Message)"
        exit 1
    }
}

# 执行主函数
Main 