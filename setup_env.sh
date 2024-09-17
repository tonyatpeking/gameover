#!/bin/bash

# Change directory to the script's directory
cd "$(dirname "$0")"

# Check if the virtual environment directory exists
if [ -d ".venv" ]; then
    printf "Virtual environment already exists. Choose:\n 1 (default) Install requirements into the existing environment.\n 2 Recreate environment.\n"
    read choice
    choice=${choice:-1}  # Default to '1' if no input is provided
    if [ "$choice" = "2" ]; then
        rm -rf .venv
        python3 -m venv .venv
        printf "Virtual environment recreated.\n"
    else
        printf "Skipping virtual environment recreation and installing new requirements.\n"
    fi
else
    python3 -m venv .venv
    printf "Virtual environment created.\n"
fi

# Activate the virtual environment
source .venv/bin/activate

# Install or update the requirements
pip install -r requirements.txt

printf "Virtual environment setup complete. To activate it, run 'source .venv/bin/activate'.\n"