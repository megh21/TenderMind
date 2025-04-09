#!/bin/bash

echo "Starting TenderMind application..."

# Check if container already exists
if docker ps -a | grep -q "tendermind"; then
    echo "Found existing tendermind container. Stopping and removing it..."
    docker stop tendermind >/dev/null 2>&1
    docker rm tendermind >/dev/null 2>&1
fi

# Create docker volume if it doesn't exist
docker volume create tendermind_data

# Start new container
docker run -d \
    --name tendermind \
    -p 8080:8080 \
    -v tendermind_data:/app/instance \
    tendermind:latest

if [ $? -eq 0 ]; then
    echo "Application started successfully!"
    echo "Access the application at http://localhost:8080"
else
    echo "Failed to start the application!"
    exit 1
fi