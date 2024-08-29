#!/bin/bash

# Check if the virtual environment directory exists
if [ -d "venv" ]; then
    read -p "Virtual environment already exists. Do you want to delete and recreate it? (y/n): " choice
    if [ "$choice" = "y" ]; then
        rm -rf venv
        python3 -m venv venv
        echo "Virtual environment recreated."
    else
        echo "Skipping virtual environment creation."
    fi
else
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate the virtual environment
source venv/bin/activate

# Install or update the requirements
pip install -r requirements.txt

echo "Virtual environment setup complete. To activate it, run 'source venv/bin/activate'."