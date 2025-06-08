#!/usr/bin/env pwsh
# 开发环境文件监控脚本

Write-Host "👀 启动开发环境文件监控..." -ForegroundColor Green
Write-Host "📁 监控目录: platform/frontend/src" -ForegroundColor Cyan
Write-Host "🔄 文件变化时将自动重新构建并部署" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止监控" -ForegroundColor Yellow

# 创建文件系统监控器
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "platform/frontend/src"
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

# 防抖动：避免短时间内多次触发
$lastBuild = [DateTime]::MinValue
$debounceSeconds = 3

# 定义事件处理
$action = {
    $now = Get-Date
    if (($now - $script:lastBuild).TotalSeconds -lt $script:debounceSeconds) {
        return
    }
    $script:lastBuild = $now
    
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    
    Write-Host "" -ForegroundColor Gray
    Write-Host "📝 检测到文件变化: $name ($changeType)" -ForegroundColor Yellow
    Write-Host "🚀 开始自动重新部署..." -ForegroundColor Green
    
    # 执行部署脚本
    & "./deploy-frontend.ps1"
    
    Write-Host "✅ 自动部署完成，继续监控..." -ForegroundColor Green
}

# 注册事件
Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $action

try {
    # 保持脚本运行
    while ($true) {
        Start-Sleep 1
    }
} finally {
    # 清理资源
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "👋 文件监控已停止" -ForegroundColor Red
} 