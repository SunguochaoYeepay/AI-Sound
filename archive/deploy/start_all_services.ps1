# AI-Sound系统启动脚本
# 启动所有必要的服务

Write-Host "=== AI-Sound系统启动脚本 ===" -ForegroundColor Green

# 检查Docker是否运行
Write-Host "检查Docker状态..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✓ Docker已安装" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker未安装或未运行，请先安装Docker Desktop" -ForegroundColor Red
    exit 1
}

# 检查Docker是否运行
try {
    docker ps | Out-Null
    Write-Host "✓ Docker服务正在运行" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker服务未运行，请启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 创建网络
Write-Host "创建Docker网络..." -ForegroundColor Yellow
docker network create ai-sound-network 2>$null
Write-Host "✓ 网络已创建或已存在" -ForegroundColor Green

# 1. 启动基础设施服务（MongoDB）
Write-Host "`n1. 启动MongoDB服务..." -ForegroundColor Cyan
Set-Location "services/infrastructure"
docker-compose -f docker-compose.mongodb.yml up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ MongoDB启动成功" -ForegroundColor Green
} else {
    Write-Host "✗ MongoDB启动失败" -ForegroundColor Red
}
Set-Location "../.."

# 等待MongoDB启动
Write-Host "等待MongoDB启动完成..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 2. 启动MegaTTS3服务
Write-Host "`n2. 启动MegaTTS3服务..." -ForegroundColor Cyan
Set-Location "MegaTTS/MegaTTS3"
# 使用简化配置启动单个实例
docker-compose -f docker-compose.production.yml up -d megatts-api-1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ MegaTTS3启动成功" -ForegroundColor Green
} else {
    Write-Host "✗ MegaTTS3启动失败" -ForegroundColor Red
}
Set-Location "../.."

# 等待MegaTTS3启动
Write-Host "等待MegaTTS3启动完成..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# 3. 检查服务状态
Write-Host "`n3. 检查服务状态..." -ForegroundColor Cyan

# 检查MongoDB
Write-Host "检查MongoDB..." -ForegroundColor Yellow
try {
    $mongoResponse = Invoke-WebRequest -Uri "http://localhost:27017" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✓ MongoDB可访问" -ForegroundColor Green
} catch {
    Write-Host "✗ MongoDB不可访问" -ForegroundColor Red
}

# 检查MegaTTS3
Write-Host "检查MegaTTS3..." -ForegroundColor Yellow
try {
    $megaResponse = Invoke-WebRequest -Uri "http://localhost:7929/health" -TimeoutSec 10 -ErrorAction Stop
    Write-Host "✓ MegaTTS3服务正常" -ForegroundColor Green
} catch {
    Write-Host "✗ MegaTTS3服务不可访问: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== 服务启动完成 ===" -ForegroundColor Green
Write-Host "现在可以启动API服务：" -ForegroundColor Cyan
Write-Host "cd services/api" -ForegroundColor White
Write-Host "python main.py" -ForegroundColor White 