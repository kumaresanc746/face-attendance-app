#!/bin/bash

# Update system
sudo apt-get update

# Install pip and system dependencies for OpenCV
sudo apt-get install -y python3-pip python3-dev libgl1 libglib2.0-0

# Install Python packages using python3 -m pip
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Start the application with Gunicorn
echo "------------------------------------------------"
echo "Setup complete. You can start the server with:"
echo "python3 -m gunicorn -w 4 -b 0.0.0.0:5000 app:app"
echo "------------------------------------------------"
