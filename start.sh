#!/bin/bash

# Voice Clipboard Start Script
cd ~/Projects/voice-clipboard

# Activate virtual environment
source venv/bin/activate

# Failsafe: kill any existing process running on port 5000 to prevent Address Already in Use errors
echo "Checking for old server instances..."
fuser -k 5000/tcp 2>/dev/null
sleep 1

# Get the local IP address on the hotspot network
LOCAL_IP=$(ip addr | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 | grep -v '127.0.0.1' | head -n 1)

echo "===================================================="
echo "          🎙️ VOICE CLIPBOARD SERVER 🎙️"
echo "===================================================="
echo ""
echo "Access it on your phone at:"
echo "👉 https://${LOCAL_IP}:5000"
echo ""
echo "Press Ctrl+C to stop the server."
echo "===================================================="

# Run the secure server
uvicorn src.main:app --host 0.0.0.0 --port 5000 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
