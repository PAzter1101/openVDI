#!/bin/bash

# Improved initialization script with better error handling and logging
# Exit on any error, undefined variables, and pipe failures
set -euo pipefail

# Function to log messages with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Function to check if command succeeded
check_command() {
    if [ $? -ne 0 ]; then
        error_exit "$1"
    fi
}

log "Starting openVDI initialization..."

# Check if docker daemon is running
log "Checking Docker daemon status..."
if ! docker ps >/dev/null 2>&1; then
    error_exit "Docker daemon is not running. Please start Docker and try again."
fi
log "Docker daemon is running."

# Prepare directories
log "Preparing directories..."

# Create init directory
if [ ! -d "./init" ]; then
    log "Creating ./init directory..."
    mkdir ./init || error_exit "Failed to create ./init directory"
else
    log "./init directory already exists."
fi

# Set permissions for init directory
log "Setting permissions for ./init directory..."
chmod -R +x ./init || error_exit "Failed to set permissions for ./init directory"

# Create record directory
if [ ! -d "./record" ]; then
    log "Creating ./record directory..."
    mkdir ./record || error_exit "Failed to create ./record directory"
else
    log "./record directory already exists."
fi

# Set permissions for record directory
log "Setting permissions for ./record directory..."
chmod -R 777 ./record || error_exit "Failed to set permissions for ./record directory"

# Generate initdb.sql
log "Generating ./init/initdb.sql using Guacamole container..."
if docker run --rm guacamole/guacamole /opt/guacamole/bin/initdb.sh --postgresql > ./init/initdb.sql; then
    log "Successfully generated ./init/initdb.sql"
    
    # Verify the file was created and has content
    if [ ! -f "./init/initdb.sql" ] || [ ! -s "./init/initdb.sql" ]; then
        error_exit "initdb.sql file was not created properly or is empty"
    fi
    
    log "Verified ./init/initdb.sql file integrity."
else
    error_exit "Failed to generate ./init/initdb.sql using Guacamole container"
fi

log "openVDI initialization completed successfully!"

