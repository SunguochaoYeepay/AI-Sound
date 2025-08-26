# MySQL启动脚本
Write-Host "[MYSQL-START] 启动MySQL服务..." -ForegroundColor Green

# 停止可能存在的MySQL进程
Get-Process -Name "mysqld" -ErrorAction SilentlyContinue | Stop-Process -Force

# 启动MySQL服务
Write-Host "正在启动MySQL..." -ForegroundColor Yellow
Start-Process -FilePath "C:\xampp\mysql\bin\mysqld.exe" -ArgumentList @(
    "--console",
    "--basedir=C:\xampp\mysql",
    "--datadir=C:\xampp\mysql\data",
    "--port=3306"
) -WindowStyle Hidden

# 等待MySQL启动
Write-Host "等待MySQL启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 测试连接
Write-Host "测试MySQL连接..." -ForegroundColor Yellow
$result = & "C:\xampp\mysql\bin\mysql.exe" -u root -e "SELECT VERSION();" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ MySQL启动成功！" -ForegroundColor Green
    Write-Host "版本信息: $result" -ForegroundColor Cyan
} else {
    Write-Host "❌ MySQL连接失败: $result" -ForegroundColor Red
}

Write-Host "MySQL启动脚本完成！" -ForegroundColor Green
