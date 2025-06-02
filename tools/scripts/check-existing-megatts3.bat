@echo off
echo Checking for existing MegaTTS3 services...

echo.
echo === Docker Containers ===
docker ps -a | findstr megatts
if errorlevel 1 (
    echo No MegaTTS3 containers found
) else (
    echo Found MegaTTS3 containers
)

echo.
echo === Running Processes ===
echo Checking port 8001 (API):
netstat -ano | findstr :8001
if errorlevel 1 (
    echo Port 8001 not in use
) else (
    echo Port 8001 is in use - API might be running
)

echo.
echo Checking port 8002 (WebUI):
netstat -ano | findstr :8002
if errorlevel 1 (
    echo Port 8002 not in use
) else (
    echo Port 8002 is in use - WebUI might be running
)

echo.
echo === Docker Images ===
docker images | findstr megatts
if errorlevel 1 (
    echo No MegaTTS3 images found
) else (
    echo Found MegaTTS3 images
)

pause