# AI-Sound 服务启动脚本
Write-Host "正在启动 AI-Sound 服务..." -ForegroundColor Green

# 启动后端服务
Write-Host "启动后端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd platform\backend; python main.py"

# 等待2秒，让后端服务启动
Start-Sleep -Seconds 2

# 启动前端服务
Write-Host "启动前端服务..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd platform\frontend; npm run dev"

Write-Host ""
Write-Host "服务启动完成！" -ForegroundColor Green
Write-Host "后端服务: http://localhost:8001" -ForegroundColor Cyan
Write-Host "前端服务: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "请等待几秒钟让服务完全启动..." -ForegroundColor Yellow 