import requests as requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from cloudproxy.providers import settings


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_ip(ip_address):
    auth = (
        settings.config["auth"]["username"] + ":" + settings.config["auth"]["password"]
    )

    proxies = {
        "http": "http://" + auth + "@" + ip_address + ":8899",
        "https": "http://" + auth + "@" + ip_address + ":8899",
    }
    s = requests.Session()
    s.proxies = proxies

    fetched_ip = requests_retry_session(session=s).get(
        "https://api.ipify.org", proxies=proxies
    )
    return fetched_ip.text


def check_alive(ip_address):
    try:
        if ip_address == fetch_ip(ip_address):
            return True
        else:
            return False
    except:
        return False
