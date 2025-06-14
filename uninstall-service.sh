#!/bin/bash

# B1T Web Analyzer Service Uninstallation Script

echo "Uninstalling B1T Web Analyzer service..."

# Stop the service if running
sudo systemctl stop b1t-analyzer.service

# Disable the service
sudo systemctl disable b1t-analyzer.service

# Remove service file
sudo rm -f /etc/systemd/system/b1t-analyzer.service

# Reload systemd daemon
sudo systemctl daemon-reload

# Reset failed state
sudo systemctl reset-failed

echo "Service uninstallation complete!"
echo "The B1T Web Analyzer service has been removed from the system."