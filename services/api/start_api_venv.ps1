#!/usr/bin/env pwsh
<#
.SYNOPSIS
    在虚拟环境中启动MegaTTS API服务

.DESCRIPTION
    这个脚本会自动激活虚拟环境并启动API服务
    支持多种启动参数

.PARAMETER ServerHost
    服务器主机地址，默认为 127.0.0.1

.PARAMETER Port
    服务器端口，默认为 9930

.PARAMETER Reload
    是否启用热重载模式

.PARAMETER Debug
    是否启用调试模式

.PARAMETER Workers
    工作进程数，默认为 1

.EXAMPLE
    .\start_api_venv.ps1
    使用默认参数启动服务

.EXAMPLE
    .\start_api_venv.ps1 -ServerHost "0.0.0.0" -Port 8000 -Reload
    在所有网络接口上启动服务，端口8000，启用热重载
#>

param(
    [string]$ServerHost = "127.0.0.1",
    [int]$Port = 9930,
    [switch]$Reload,
    [switch]$Debug,
    [int]$Workers = 1
)

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

Write-Host "=== MegaTTS API 服务启动脚本 ===" -ForegroundColor Green
Write-Host "项目根目录: $ProjectRoot" -ForegroundColor Cyan
Write-Host "API目录: $ScriptDir" -ForegroundColor Cyan

# 检查虚拟环境是否存在
$VenvPath = Join-Path $ScriptDir "venv"
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"

if (-not (Test-Path $ActivateScript)) {
    Write-Host "错误: 虚拟环境不存在，请先创建虚拟环境" -ForegroundColor Red
    Write-Host "运行以下命令创建虚拟环境:" -ForegroundColor Yellow
    Write-Host "  python -m venv $VenvPath" -ForegroundColor Yellow
    Write-Host "  & $ActivateScript" -ForegroundColor Yellow
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 检查main.py是否存在
$MainScript = Join-Path $ScriptDir "main.py"
if (-not (Test-Path $MainScript)) {
    Write-Host "错误: main.py 不存在: $MainScript" -ForegroundColor Red
    exit 1
}

# 激活虚拟环境
Write-Host "正在激活虚拟环境..." -ForegroundColor Yellow
try {
    & $ActivateScript
    if ($LASTEXITCODE -ne 0) {
        throw "激活虚拟环境失败"
    }
} catch {
    Write-Host "错误: 无法激活虚拟环境: $_" -ForegroundColor Red
    exit 1
}

# 设置环境变量
$env:MODEL_PATH = Join-Path $ProjectRoot "data\checkpoints\megatts3_base.pth"
$env:OUTPUT_DIR = Join-Path $ScriptDir "output"
$env:VOICE_FEATURES_DIR = Join-Path $ProjectRoot "data\voice_features"

Write-Host "环境变量设置:" -ForegroundColor Cyan
Write-Host "  MODEL_PATH: $env:MODEL_PATH" -ForegroundColor Gray
Write-Host "  OUTPUT_DIR: $env:OUTPUT_DIR" -ForegroundColor Gray
Write-Host "  VOICE_FEATURES_DIR: $env:VOICE_FEATURES_DIR" -ForegroundColor Gray

# 创建必要的目录
$Directories = @(
    $env:OUTPUT_DIR,
    (Join-Path $env:OUTPUT_DIR "single"),
    (Join-Path $env:OUTPUT_DIR "novels"),
    (Join-Path $env:OUTPUT_DIR "previews"),
    $env:VOICE_FEATURES_DIR,
    (Split-Path $env:MODEL_PATH -Parent)
)

foreach ($Dir in $Directories) {
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
        Write-Host "创建目录: $Dir" -ForegroundColor Green
    }
}

# 构建启动命令
$Command = @("python", $MainScript, "--host", $ServerHost, "--port", $Port.ToString())

if ($Reload) {
    $Command += "--reload"
    Write-Host "启用热重载模式" -ForegroundColor Yellow
}

if ($Debug) {
    $Command += "--debug"
    Write-Host "启用调试模式" -ForegroundColor Yellow
}

if ($Workers -gt 1 -and -not $Reload) {
    $Command += @("--workers", $Workers.ToString())
    Write-Host "使用 $Workers 个工作进程" -ForegroundColor Yellow
}

# 显示启动信息
Write-Host "`n=== 启动信息 ===" -ForegroundColor Green
Write-Host "服务地址: http://${ServerHost}:${Port}" -ForegroundColor Cyan
Write-Host "健康检查: http://${ServerHost}:${Port}/health" -ForegroundColor Cyan
Write-Host "API文档: http://${ServerHost}:${Port}/docs" -ForegroundColor Cyan
Write-Host "`n按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "启动命令: $($Command -join ' ')" -ForegroundColor Gray

# 启动服务
try {
    Set-Location $ScriptDir
    & $Command[0] $Command[1..($Command.Length-1)]
} catch {
    Write-Host "`n错误: 启动服务失败: $_" -ForegroundColor Red
    exit 1
} finally {
    Write-Host "`n服务已停止" -ForegroundColor Yellow
} 