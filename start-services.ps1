# AI-Sound Platform 服务启动脚本
# 用于启动前后端开发服务器

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "backend", "frontend", "status", "stop")]
    [string]$Action = "all"
)

Write-Host "🚀 AI-Sound Platform 服务管理器" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

function Start-Backend {
    Write-Host "🎯 启动后端服务..." -ForegroundColor Yellow
    
    # 检查Python环境
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ Python环境: $pythonVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Python未安装或不在PATH中" -ForegroundColor Red
        return $false
    }
    
    # 启动后端
    Write-Host "📍 启动目录: $(Get-Location)\platform\backend" -ForegroundColor Blue
    
    $backendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD\platform\backend
        python main.py
    }
    
    Write-Host "✅ 后端服务已在后台启动 (Job ID: $($backendJob.Id))" -ForegroundColor Green
    Write-Host "🌐 后端地址: http://localhost:8000" -ForegroundColor Blue
    Write-Host "📚 API文档: http://localhost:8000/docs" -ForegroundColor Blue
    
    return $backendJob
}

function Start-Frontend {
    Write-Host "🎯 启动前端服务..." -ForegroundColor Yellow
    
    # 检查Node.js环境
    try {
        $nodeVersion = node --version 2>&1
        Write-Host "✅ Node.js环境: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "❌ Node.js未安装或不在PATH中" -ForegroundColor Red
        return $false
    }
    
    # 检查依赖
    if (-not (Test-Path "platform\frontend\node_modules")) {
        Write-Host "📦 正在安装前端依赖..." -ForegroundColor Yellow
        Set-Location platform\frontend
        npm install
        Set-Location ..\..
    }
    
    # 启动前端
    Write-Host "📍 启动目录: $(Get-Location)\platform\frontend" -ForegroundColor Blue
    
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD\platform\frontend
        npm run dev
    }
    
    Write-Host "✅ 前端服务已在后台启动 (Job ID: $($frontendJob.Id))" -ForegroundColor Green
    Write-Host "🌐 前端地址: http://localhost:3000" -ForegroundColor Blue
    
    return $frontendJob
}

function Get-ServiceStatus {
    Write-Host "🔍 检查服务状态..." -ForegroundColor Yellow
    
    # 检查运行中的Jobs
    $jobs = Get-Job | Where-Object { $_.State -eq "Running" }
    
    if ($jobs.Count -gt 0) {
        Write-Host "✅ 发现 $($jobs.Count) 个运行中的服务:" -ForegroundColor Green
        foreach ($job in $jobs) {
            Write-Host "  - Job ID: $($job.Id), Name: $($job.Name)" -ForegroundColor Blue
        }
    } else {
        Write-Host "⚠️ 没有发现运行中的后台服务" -ForegroundColor Yellow
    }
    
    # 检查端口占用
    try {
        $ports = @(3000, 8000)
        foreach ($port in $ports) {
            $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
            if ($connection) {
                Write-Host "✅ 端口 $port 已被占用 (PID: $($connection.OwningProcess))" -ForegroundColor Green
            } else {
                Write-Host "❌ 端口 $port 未被占用" -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "⚠️ 无法检查端口状态" -ForegroundColor Yellow
    }
}

function Stop-Services {
    Write-Host "🛑 停止所有服务..." -ForegroundColor Yellow
    
    $jobs = Get-Job
    if ($jobs.Count -gt 0) {
        foreach ($job in $jobs) {
            Write-Host "🔄 停止 Job ID: $($job.Id)" -ForegroundColor Blue
            Stop-Job -Id $job.Id
            Remove-Job -Id $job.Id -Force
        }
        Write-Host "✅ 所有后台服务已停止" -ForegroundColor Green
    } else {
        Write-Host "⚠️ 没有运行中的后台服务" -ForegroundColor Yellow
    }
}

# 主逻辑
switch ($Action) {
    "backend" {
        $job = Start-Backend
        if ($job) {
            Write-Host "`n💡 使用 'Get-Job' 查看任务状态" -ForegroundColor Cyan
            Write-Host "💡 使用 'Receive-Job -Id $($job.Id)' 查看输出" -ForegroundColor Cyan
        }
    }
    "frontend" {
        $job = Start-Frontend
        if ($job) {
            Write-Host "`n💡 使用 'Get-Job' 查看任务状态" -ForegroundColor Cyan
            Write-Host "💡 使用 'Receive-Job -Id $($job.Id)' 查看输出" -ForegroundColor Cyan
        }
    }
    "all" {
        $backendJob = Start-Backend
        Start-Sleep -Seconds 3  # 等待后端启动
        $frontendJob = Start-Frontend
        
        Write-Host "`n🎉 所有服务启动完成!" -ForegroundColor Green
        Write-Host "📋 服务概览:" -ForegroundColor Cyan
        Write-Host "  - 后端: http://localhost:8000" -ForegroundColor Blue
        Write-Host "  - 前端: http://localhost:3000" -ForegroundColor Blue
        Write-Host "  - API文档: http://localhost:8000/docs" -ForegroundColor Blue
        
        Write-Host "`n💡 管理命令:" -ForegroundColor Cyan
        Write-Host "  - 查看状态: .\start-services.ps1 -Action status" -ForegroundColor Gray
        Write-Host "  - 停止服务: .\start-services.ps1 -Action stop" -ForegroundColor Gray
        Write-Host "  - 查看输出: Get-Job | Receive-Job" -ForegroundColor Gray
    }
    "status" {
        Get-ServiceStatus
    }
    "stop" {
        Stop-Services
    }
}

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "🎯 AI-Sound Platform 服务管理器完成" -ForegroundColor Cyan 