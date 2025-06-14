#!/bin/bash

# B1T Web Analyzer Service Installation Script

echo "Installing B1T Web Analyzer as a system service..."

# Copy service file to systemd directory
cp /root/b1t-web-analyzer/b1t-analyzer.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable b1t-analyzer.service

# Start the service
sudo systemctl start b1t-analyzer.service

# Check service status
sudo systemctl status b1t-analyzer.service

echo ""
echo "Service installation complete!"
echo "You can now use the following commands to manage the service:"
echo "  sudo systemctl start b1t-analyzer    # Start the service"
echo "  sudo systemctl stop b1t-analyzer     # Stop the service"
echo "  sudo systemctl restart b1t-analyzer  # Restart the service"
echo "  sudo systemctl status b1t-analyzer   # Check service status"
echo "  sudo systemctl enable b1t-analyzer   # Enable auto-start on boot"
echo "  sudo systemctl disable b1t-analyzer  # Disable auto-start on boot"
echo ""
echo "View logs with: sudo journalctl -u b1t-analyzer -f"