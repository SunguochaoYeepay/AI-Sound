# 强制终止占用8001端口的进程
Write-Host "🔍 查找占用8001端口的进程..."

# 查找占用8001端口的进程
$processes = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | Select-Object OwningProcess -Unique

if ($processes) {
    foreach ($proc in $processes) {
        if ($proc.OwningProcess) {
            Write-Host "🔪 终止进程 PID: $($proc.OwningProcess)"
            Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "✅ 已终止所有占用8001端口的进程"
} else {
    Write-Host "ℹ️ 没有找到占用8001端口的进程"
}

# 额外终止所有Python进程（以防万一）
Write-Host "🔪 终止所有Python进程..."
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "🎯 端口清理完成，可以重新启动后端服务"
Write-Host "请运行: cd platform\backend && python main.py" 