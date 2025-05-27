#!/bin/bash

# Print a message indicating it's starting the process
echo "Starting the Docker build and run process..."

# Check if Docker is installed and available in the PATH
if ! command -v docker &> /dev/null
then
    echo "Error: Docker is not installed or not found in PATH. Please install Docker and try again."
    exit 1
fi

# Check if Docker Compose is installed and available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null
then
    echo "Error: Docker Compose is not installed or not found in PATH. Please install Docker Compose and try again."
    exit 1
fi

# Attempt to build the Docker image
echo "Building the Docker image..."
if ! docker build -t bitcoin-wallet-api .
then
    echo "Error: Docker image build failed."
    exit 1
else
    echo "Docker image built successfully."
fi

# Attempt to start the bitcoin-wallet service using Docker Compose
echo "Starting the bitcoin-wallet service..."
if command -v docker-compose &> /dev/null
then
    if ! docker-compose up -d bitcoin-wallet
    then
        echo "Error: Failed to start the bitcoin-wallet service using docker-compose."
        exit 1
    fi
elif docker compose version &> /dev/null
then
    if ! docker compose up -d bitcoin-wallet
    then
        echo "Error: Failed to start the bitcoin-wallet service using docker compose."
        exit 1
    fi
else
    # This case should ideally not be reached due to the earlier check,
    # but as a fallback.
    echo "Error: Docker Compose command not found."
    exit 1
fi

echo "Bitcoin-wallet service started successfully. The API should be accessible."

exit 0
