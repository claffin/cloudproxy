#!/bin/bash
sudo apt-get -y update
sudo apt-get install -y ca-certificates 3proxy

# Create 3proxy config directory and config
sudo mkdir -p /etc/3proxy
sudo cat > /etc/3proxy/3proxy.cfg << EOF
# Main settings
daemon
maxconn 100
nserver 1.1.1.1
nserver 8.8.8.8
nscache 65536
timeouts 1 5 30 60 180 1800 15 60

# Access control and authentication
users username:CL:password
auth strong cache 60

# Privacy settings
deny * * 127.0.0.1,192.168.1.1-192.168.255.255
# IP-based access will be configured here if enabled
allow username * *

# Proxy settings
proxy -p8899 -n -a
EOF

# Create log directory
sudo mkdir -p /var/log/3proxy

# Setup firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp
sudo ufw allow 8899/tcp
sudo ufw --force enable

# Start service
sudo systemctl enable 3proxy
sudo systemctl start 3proxy
