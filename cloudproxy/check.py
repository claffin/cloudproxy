import requests as requests

from cloudproxy.providers.digitalocean.config import username, password


def check_alive(ip_address):
    auth = username + ":" + password
    proxies = {"http": "http://" + auth + "@" + ip_address + ":8899", "https": "http://" + auth + "@" + ip_address + ":8899"}
    fetched_ip = requests.get("https://api.ipify.org", proxies=proxies).text
    if ip_address == fetched_ip:
        return True
    else:
        return False
