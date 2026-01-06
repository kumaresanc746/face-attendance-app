#!/bash/bin

# Update system and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev libgl1-mesa-glx libglib2.0-0

# Install Python packages
pip3 install -r requirements.txt

# Start the application with Gunicorn
echo "Setup complete. You can start the server with:"
echo "gunicorn -w 4 -b 0.0.0.0:5000 app:app"
