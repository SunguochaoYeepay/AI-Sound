@echo off
echo Checking existing MegaTTS3 services...

echo Checking for running containers...
docker ps | findstr megatts3

echo.
echo Checking for stopped containers...
docker ps -a | findstr megatts3

echo.
echo Starting existing containers (if any)...
docker start megatts3-api 2>nul
docker start megatts3-webui 2>nul
docker start nginx-gateway 2>nul

echo.
echo Current service status:
echo Checking API (port 8001)...
netstat -ano | findstr :8001

echo Checking WebUI (port 8002)...
netstat -ano | findstr :8002

echo Checking Gateway (port 7929)...
netstat -ano | findstr :7929

echo.
echo If services are running:
echo - Gateway: http://localhost:7929
echo - MegaTTS3 WebUI: http://localhost:7929/ui/megatts3/
echo - MegaTTS3 API: http://localhost:7929/api/megatts3/
echo - Health Check: http://localhost:7929/health

pause