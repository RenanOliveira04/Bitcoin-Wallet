@echo off
REM Script to build and run the Docker image for bitcoin-wallet-api on Windows

echo Starting the Docker build and run process...

REM Check if Docker is installed and available in the PATH
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not found in PATH. Please install Docker and try again.
    exit /b 1
)

REM Check if Docker Compose is installed and available
set COMPOSE_CMD=
docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    set COMPOSE_CMD=docker-compose
) else (
    docker compose version >nul 2>&1
    if %errorlevel% equ 0 (
        set COMPOSE_CMD=docker compose
    )
)

if not defined COMPOSE_CMD (
    echo Error: Docker Compose is not installed or not found in PATH. Please install Docker Compose and try again.
    exit /b 1
)

REM Attempt to build the Docker image
echo Building the Docker image...
docker build -t bitcoin-wallet-api .
if %errorlevel% neq 0 (
    echo Error: Docker image build failed.
    exit /b 1
) else (
    echo Docker image built successfully.
)

REM Attempt to start the bitcoin-wallet service using Docker Compose
echo Starting the bitcoin-wallet service...
%COMPOSE_CMD% up -d bitcoin-wallet
if %errorlevel% neq 0 (
    echo Error: Failed to start the bitcoin-wallet service using %COMPOSE_CMD%.
    exit /b 1
)

echo Bitcoin-wallet service started successfully. The API should be accessible.

exit /b 0
