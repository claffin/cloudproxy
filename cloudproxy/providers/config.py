import os
import requests
from cloudproxy.providers import settings


__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def set_auth(username, password):
    
    with open(os.path.join(__location__, "user_data.sh")) as file:
        filedata = file.read()

    if settings.config["no_auth"]:
        # Remove auth configuration for 3proxy
        filedata = filedata.replace('users username:CL:password\nauth strong cache 60\n', '')
        filedata = filedata.replace('allow username * *', 'allow * * *')
    else:
        # Replace username and password in 3proxy config
        filedata = filedata.replace("username", username)
        filedata = filedata.replace("password", password)

    if settings.config["only_host_ip"]:
        ip_address = requests.get('https://ipecho.net/plain').text.strip()
        # Update UFW rules
        filedata = filedata.replace("sudo ufw allow 22/tcp", f"sudo ufw allow from {ip_address} to any port 22 proto tcp")
        filedata = filedata.replace("sudo ufw allow 8899/tcp", f"sudo ufw allow from {ip_address} to any port 8899 proto tcp")
        # Update 3proxy access rule to require both username and IP
        filedata = filedata.replace("allow username * *", f"allow username * {ip_address}")

    return filedata
