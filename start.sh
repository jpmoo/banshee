#!/bin/bash

# Banshee RPG Startup Script

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Please create it first."
    exit 1
fi

# Run the game
python main.py

# Deactivate virtual environment when done
deactivate








