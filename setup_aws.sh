#!/bin/bash

# Update system
sudo apt-get update

# Install venv and system dependencies for OpenCV
sudo apt-get install -y python3-venv python3-full python3-dev libgl1 libglib2.0-0

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages inside venv
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start the application with Gunicorn
echo "------------------------------------------------"
echo "Setup complete. You can start the server with:"
echo "./venv/bin/python -m gunicorn -w 4 -b 0.0.0.0:5000 app:app"
echo "------------------------------------------------"
