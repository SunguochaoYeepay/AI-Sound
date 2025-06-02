@echo off
echo Stopping AI-Sound Microservices Platform...

docker-compose -f docker-compose.microservices.yml down

echo All services stopped.
pause