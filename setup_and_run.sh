#!/bin/bash

# Exit on error
set -e

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required Python packages
pip install -r requirements.txt

# Run the bot
python bot.py
