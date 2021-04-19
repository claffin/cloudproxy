import requests as requests

from cloudproxy.providers.settings import username, password


def check_alive(ip_address):
    auth = username + ":" + password
    proxies = {"http": "http://" + auth + "@" + ip_address + ":8899", "https": "http://" + auth + "@" + ip_address + ":8899"}
    try:
        fetched_ip = requests.get("https://api.ipify.org", proxies=proxies)
        if ip_address == fetched_ip.text:
            return True
        else:
            return False
    except:
        return False
