@echo off
echo AI-Sound Quick Start (No Build Required)
echo =========================================

echo Step 1: Checking existing services...
netstat -ano | findstr :8001 >nul 2>&1
if not errorlevel 1 (
    echo ✅ MegaTTS3 API already running on port 8001
    set API_RUNNING=1
) else (
    echo ❌ No API service on port 8001
    set API_RUNNING=0
)

netstat -ano | findstr :8002 >nul 2>&1
if not errorlevel 1 (
    echo ✅ MegaTTS3 WebUI already running on port 8002
    set WEBUI_RUNNING=1
) else (
    echo ❌ No WebUI service on port 8002
    set WEBUI_RUNNING=0
)

echo.
echo Step 2: Choose startup strategy...

if %API_RUNNING%==1 if %WEBUI_RUNNING%==1 (
    echo 🚀 Both services running - Starting gateway only...
    docker-compose -f docker-compose.external.yml up -d
    echo ✅ Gateway started! Access: http://localhost:7929
    goto :end
)

echo 🔄 Need to start MegaTTS3 services...
echo Checking for existing containers...
docker ps -a | findstr megatts3 >nul 2>&1
if not errorlevel 1 (
    echo ✅ Found existing containers - Starting them...
    docker start megatts3-api megatts3-webui 2>nul
    timeout /t 5 >nul
    docker-compose -f docker-compose.external.yml up -d
) else (
    echo 📦 Starting full microservices (with existing images)...
    docker-compose -f docker-compose.microservices.yml up -d --no-build
)

:end
echo.
echo 🎉 Services started!
echo - Gateway: http://localhost:7929
echo - WebUI: http://localhost:7929/ui/megatts3/
echo - API: http://localhost:7929/api/megatts3/
echo - Health: http://localhost:7929/health
pause