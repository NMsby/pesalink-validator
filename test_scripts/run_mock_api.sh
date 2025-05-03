#!/bin/bash

# Script to run the mock PesaLink API server

echo "Starting Mock PesaLink API Server"
echo "================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check for Flask
python -c "import flask" 2>/dev/null
# shellcheck disable=SC2181
if [ $? -ne 0 ]; then
    echo "Installing Flask..."
    pip install flask
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables
export FLASK_APP=test_scripts/mock_pesalink_api.py

# Run in background or foreground
if [ "$1" == "--background" ] || [ "$1" == "-b" ]; then
    # Run in background
    echo "Starting server in background mode..."
    python test_scripts/mock_pesalink_api.py > logs/mock_api.log 2>&1 &
    PID=$!
    echo "Server started with PID: $PID"
    echo "To stop the server: kill $PID"
    echo "Logs available at: logs/mock_api.log"
else
    # Run in foreground
    echo "Starting server in foreground mode..."
    echo "Press Ctrl+C to stop the server"
    python test_scripts/mock_pesalink_api.py
fi