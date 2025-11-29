#!/bin/bash
# Preview script for quest location maps

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 preview_quest_maps.py



cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 preview_quest_maps.py

