Write-Host "开始构建前端..." -ForegroundColor Green

# 进入前端目录
Set-Location platform/frontend

# 检查Node.js环境
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "使用本地Node.js构建" -ForegroundColor Blue
    npm run build
} elseif (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "使用Docker构建" -ForegroundColor Blue
    $currentPath = (Get-Location).Path
    docker run --rm -v "${currentPath}:/app" -w /app node:18-alpine sh -c "npm install && npm run build"
} else {
    Write-Host "错误：未找到Node.js或Docker环境" -ForegroundColor Red
    exit 1
}

Write-Host "前端构建完成" -ForegroundColor Green
Write-Host "重启nginx容器..." -ForegroundColor Yellow
docker restart ai-sound-nginx
Write-Host "构建完成！" -ForegroundColor Green 