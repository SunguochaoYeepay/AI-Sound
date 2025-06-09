#!/usr/bin/env powershell
# AI-Sound Backend 虚拟环境设置脚本

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("create", "activate", "install", "run", "clean")]
    [string]$Action = "create"
)

$VenvPath = ".\venv"
$PythonVersion = "3.10"  # MegaTTS兼容的Python版本

Write-Host "🚀 AI-Sound Backend 虚拟环境管理器" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

function Test-PythonInstalled {
    try {
        $pythonCmd = Get-Command python -ErrorAction Stop
        $version = & python --version 2>&1
        Write-Host "✅ 发现Python: $version" -ForegroundColor Green
        Write-Host "📍 路径: $($pythonCmd.Source)" -ForegroundColor Blue
        return $true
    } catch {
        Write-Host "❌ Python未找到，请先安装Python $PythonVersion" -ForegroundColor Red
        Write-Host "💡 下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
        return $false
    }
}

function New-VirtualEnv {
    Write-Host "🎯 创建虚拟环境..." -ForegroundColor Yellow
    
    if (-not (Test-PythonInstalled)) {
        return $false
    }
    
    # 删除现有虚拟环境
    if (Test-Path $VenvPath) {
        Write-Host "🧹 清理现有虚拟环境..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvPath
    }
    
    # 创建虚拟环境
    try {
        Write-Host "📦 创建虚拟环境: $VenvPath" -ForegroundColor Blue
        & python -m venv $VenvPath
        
        if ($LASTEXITCODE -ne 0) {
            throw "虚拟环境创建失败"
        }
        
        Write-Host "✅ 虚拟环境创建成功" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ 虚拟环境创建失败: $_" -ForegroundColor Red
        return $false
    }
}

function Install-Dependencies {
    Write-Host "🎯 安装依赖包..." -ForegroundColor Yellow
    
    $activateScript = "$VenvPath\Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        Write-Host "❌ 虚拟环境不存在，请先运行: .\setup-venv.ps1 -Action create" -ForegroundColor Red
        return $false
    }
    
    try {
        # 激活虚拟环境
        & $activateScript
        
        # 升级pip
        Write-Host "📦 升级pip..." -ForegroundColor Blue
        & python -m pip install --upgrade pip
        
        # 安装基础依赖
        Write-Host "📦 安装基础依赖..." -ForegroundColor Blue
        & pip install wheel setuptools
        
        # 安装后端开发依赖（轻量级，不包含MegaTTS依赖）
        Write-Host "📦 安装后端开发依赖..." -ForegroundColor Blue
        & pip install -r requirements-dev.txt
        
        Write-Host "✅ 依赖安装完成" -ForegroundColor Green
        return $true
        
    } catch {
        Write-Host "❌ 依赖安装失败: $_" -ForegroundColor Red
        return $false
    }
}

function Start-Backend {
    Write-Host "🎯 启动后端服务..." -ForegroundColor Yellow
    
    $activateScript = "$VenvPath\Scripts\Activate.ps1"
    if (-not (Test-Path $activateScript)) {
        Write-Host "❌ 虚拟环境不存在，请先运行完整设置" -ForegroundColor Red
        return $false
    }
    
    try {
        # 激活虚拟环境并启动
        Write-Host "🔄 激活虚拟环境并启动服务..." -ForegroundColor Blue
        
        # 创建启动脚本
        $startScript = @"
& '$activateScript'
Write-Host "🌐 虚拟环境已激活" -ForegroundColor Green
Write-Host "🚀 启动后端服务..." -ForegroundColor Yellow
& python main.py
"@
        
        $scriptPath = "start-backend-temp.ps1"
        $startScript | Out-File -FilePath $scriptPath -Encoding UTF8
        
        # 执行启动脚本
        & powershell -ExecutionPolicy Bypass -File $scriptPath
        
        # 清理临时脚本
        Remove-Item $scriptPath -ErrorAction SilentlyContinue
        
    } catch {
        Write-Host "❌ 启动失败: $_" -ForegroundColor Red
        return $false
    }
}

function Remove-VirtualEnv {
    Write-Host "🎯 清理虚拟环境..." -ForegroundColor Yellow
    
    if (Test-Path $VenvPath) {
        Remove-Item -Recurse -Force $VenvPath
        Write-Host "✅ 虚拟环境已清理" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 虚拟环境不存在" -ForegroundColor Yellow
    }
}

function Show-ActivateCommand {
    Write-Host ""
    Write-Host "💡 手动激活虚拟环境命令:" -ForegroundColor Cyan
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 退出虚拟环境命令:" -ForegroundColor Cyan  
    Write-Host "   deactivate" -ForegroundColor Gray
}

# 主逻辑
switch ($Action) {
    "create" {
        if (New-VirtualEnv) {
            Write-Host ""
            Write-Host "🎉 虚拟环境创建完成!" -ForegroundColor Green
            Write-Host "📋 下一步: .\setup-venv.ps1 -Action install" -ForegroundColor Cyan
            Show-ActivateCommand
        }
    }
    "install" {
        if (Install-Dependencies) {
            Write-Host ""
            Write-Host "🎉 依赖安装完成!" -ForegroundColor Green
            Write-Host "📋 下一步: .\setup-venv.ps1 -Action run" -ForegroundColor Cyan
            Show-ActivateCommand
        }
    }
    "run" {
        Start-Backend
    }
    "activate" {
        $activateScript = "$VenvPath\Scripts\Activate.ps1"
        if (Test-Path $activateScript) {
            Write-Host "🔄 激活虚拟环境..." -ForegroundColor Blue
            & $activateScript
            Show-ActivateCommand
        } else {
            Write-Host "❌ 虚拟环境不存在" -ForegroundColor Red
        }
    }
    "clean" {
        Remove-VirtualEnv
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "🎯 AI-Sound Backend 环境管理器完成" -ForegroundColor Cyan