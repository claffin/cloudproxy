import os
import requests
from cloudproxy.providers import settings


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def set_auth(username, password):
    
    with open(os.path.join(__location__, "user_data.sh")) as file:
        filedata = file.read()

    if settings.config["no_auth"]:
        # Remove auth configuration for tinyproxy
        filedata = filedata.replace('\nBasicAuth PROXY_USERNAME PROXY_PASSWORD\n', '\n')
    else:
        # Replace username and password in tinyproxy config
        filedata = filedata.replace("PROXY_USERNAME", username)
        filedata = filedata.replace("PROXY_PASSWORD", password)

    if settings.config["only_host_ip"]:
        ip_address = requests.get('https://ipecho.net/plain').text.strip()
        # Update UFW rules
        filedata = filedata.replace("sudo ufw allow 22/tcp", f"sudo ufw allow from {ip_address} to any port 22 proto tcp")
        filedata = filedata.replace("sudo ufw allow 8899/tcp", f"sudo ufw allow from {ip_address} to any port 8899 proto tcp")
        # Update tinyproxy access rule
        filedata = filedata.replace("Allow 127.0.0.1", f"Allow 127.0.0.1\nAllow {ip_address}")
    else:
        # When ONLY_HOST_IP is False, allow connections from any IP
        filedata = filedata.replace("Allow 127.0.0.1", "Allow 0.0.0.0/0")

    return filedata
