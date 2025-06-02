#!/bin/bash
echo "Starting AI-Sound Microservices Platform..."

echo "Building MegaTTS3 image..."
docker build -f services/tts-services/megatts3/Dockerfile -t megatts3:latest .

echo "Starting services..."
docker-compose -f docker-compose.microservices.yml up -d

echo "Services started! Access points:"
echo "- Gateway: http://localhost:7929"
echo "- MegaTTS3 WebUI: http://localhost:7929/ui/megatts3/"
echo "- MegaTTS3 API: http://localhost:7929/api/megatts3/"
echo "- Health Check: http://localhost:7929/health"