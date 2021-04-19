#!/bin/bash
apt-get -y update
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo apt update
apt-get -y install docker-ce docker-ce-cli containerd.io
docker run -d -p 8899:8899 --rm abhinavsingh/proxy.py:v2.3.1 --hostname 0.0.0.0 --basic-auth username:password
ufw default deny incoming
ufw default allow outgoing
ufw allow 8899/tcp
ufw --force enable