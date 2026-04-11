#!/bin/bash
# LLM Wiki Agent - Demo Launcher (Linux/Mac)

echo "========================================"
echo "LLM Wiki Agent - Demo Launcher"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if dependencies are installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Launch the demo
echo ""
echo "Starting demo server..."
echo "URL: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""
python3 demo/app.py
