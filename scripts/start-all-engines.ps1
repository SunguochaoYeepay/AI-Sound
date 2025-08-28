# AI-Sound 所有引擎启动脚本
# 设置UTF-8编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 AI-Sound 引擎服务管理器" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# 启动TangoFlux服务
Write-Host "🎯 启动TangoFlux环境音生成服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; .\scripts\start-tangoflux.ps1"

# 等待2秒
Start-Sleep -Seconds 2

# 启动SongGeneration服务
Write-Host "🎵 启动SongGeneration音乐生成服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; .\scripts\start-songgeneration.ps1"

# 等待2秒
Start-Sleep -Seconds 2

# 启动MegaTTS3服务
Write-Host "🎤 启动MegaTTS3语音合成服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; .\scripts\start-megatts3.ps1"

Write-Host ""
Write-Host "✅ 所有引擎服务启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 服务地址:" -ForegroundColor Blue
Write-Host "  TangoFlux环境音生成: http://localhost:7930" -ForegroundColor Cyan
Write-Host "  SongGeneration音乐生成: http://localhost:7862" -ForegroundColor Cyan
Write-Host "  MegaTTS3语音合成: http://localhost:7929" -ForegroundColor Cyan
Write-Host ""
Write-Host "请等待几秒钟让服务完全启动..." -ForegroundColor Yellow
Write-Host "每个服务都在独立的PowerShell窗口中运行" -ForegroundColor Yellow
