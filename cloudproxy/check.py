import requests as requests

from cloudproxy.providers import settings


def fetch_ip(ip_address):
    auth = (
        settings.config["auth"]["username"] + ":" + settings.config["auth"]["password"]
    )
    proxies = {
        "http": "http://" + auth + "@" + ip_address + ":8899",
        "https": "http://" + auth + "@" + ip_address + ":8899",
    }
    fetched_ip = requests.get("https://api.ipify.org", proxies=proxies)
    return fetched_ip.text


def check_alive(ip_address):
    try:
        if ip_address == fetch_ip(ip_address):
            return True
        else:
            return False
    except:
        return False
