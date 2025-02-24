#!/bin/bash

# Update package list and install required packages
sudo apt-get update
sudo apt-get install -y ca-certificates tinyproxy

# Configure tinyproxy
sudo cat > /etc/tinyproxy/tinyproxy.conf << EOF
User tinyproxy
Group tinyproxy
Port 8899
Timeout 600
DefaultErrorFile "/usr/share/tinyproxy/default.html"
StatFile "/usr/share/tinyproxy/stats.html"
LogFile "/var/log/tinyproxy/tinyproxy.log"
LogLevel Info
PidFile "/run/tinyproxy/tinyproxy.pid"
MaxClients 100
MinSpareServers 5
MaxSpareServers 20
StartServers 10
MaxRequestsPerChild 0
Allow 127.0.0.1
ViaProxyName "tinyproxy"
ConnectPort 443
ConnectPort 563
BasicAuth PROXY_USERNAME PROXY_PASSWORD
EOF

# Setup firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 8899/tcp
sudo ufw --force enable

# Enable and start service
sudo systemctl enable tinyproxy
sudo systemctl restart tinyproxy

# Wait for service to start
sleep 5
