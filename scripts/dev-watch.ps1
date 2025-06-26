# AI-Sound 开发环境监控脚本
# 监控文件变化并自动重启服务

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("backend", "frontend", "all")]
    [string]$Service = "all"
)

Write-Host "🔍 AI-Sound 开发监控启动" -ForegroundColor Cyan
Write-Host "监控服务: $Service" -ForegroundColor Yellow

# 检查是否安装了nodemon
function Test-Nodemon {
    try {
        nodemon --version | Out-Null
        return $true
    } catch {
        Write-Host "❌ nodemon未安装，请运行: npm install -g nodemon" -ForegroundColor Red
        return $false
    }
}

# 监控后端
function Watch-Backend {
    Write-Host "🎯 启动后端监控..." -ForegroundColor Green
    Set-Location platform/backend
    
    # 使用nodemon监控Python文件
    nodemon --exec "python main.py" --ext py --ignore "__pycache__/*" --ignore "*.pyc"
    
    Set-Location ../..
}

# 监控前端
function Watch-Frontend {
    Write-Host "🎯 启动前端监控..." -ForegroundColor Green
    Set-Location platform/frontend
    
    # Vue开发服务器已经内置热重载
    npm run dev
    
    Set-Location ../..
}

# 主逻辑
if (-not (Test-Nodemon)) {
    exit 1
}

switch ($Service) {
    "backend" {
        Watch-Backend
    }
    "frontend" {
        Watch-Frontend
    }
    "all" {
        Write-Host "🚀 启动全栈监控模式..." -ForegroundColor Green
        
        # 在后台启动后端监控
        $backendJob = Start-Job -ScriptBlock {
            Set-Location $using:PWD/platform/backend
            nodemon --exec "python main.py" --ext py --ignore "__pycache__/*" --ignore "*.pyc"
        }
        
        Write-Host "✅ 后端监控已启动 (Job ID: $($backendJob.Id))" -ForegroundColor Green
        
        # 前台启动前端监控
        Watch-Frontend
    }
} 