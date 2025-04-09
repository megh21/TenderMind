#!/bin/bash

echo "Building Docker image..."
docker build -t tendermind:latest .

if [ $? -eq 0 ]; then
    echo "Build completed successfully!"
else
    echo "Build failed!"
    exit 1
fi