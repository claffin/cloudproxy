import itertools
import datetime

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers import settings
from cloudproxy.providers.hetzner.functions import list_proxies, delete_proxy, create_proxy
from cloudproxy.providers.settings import config, delete_queue, restart_queue


def hetzner_deployment(min_scaling):
    total_proxies = len(list_proxies())
    if min_scaling < total_proxies:
        logger.info("Overprovisioned: Hetzner destroying.....")
        for proxy in itertools.islice(
                list_proxies(), 0, (total_proxies - min_scaling)
        ):
            delete_proxy(proxy)
            logger.info("Destroyed: Hetzner -> " + str(proxy.public_net.ipv4.ip))
    if min_scaling - total_proxies < 1:
        logger.info("Minimum Hetzner proxies met")
    else:
        total_deploy = min_scaling - total_proxies
        logger.info("Deploying: " + str(total_deploy) + " Hetzner proxy")
        for _ in range(total_deploy):
            create_proxy()
            logger.info("Deployed")
    return len(list_proxies())


def hetzner_check_alive():
    ip_ready = []
    for proxy in list_proxies():
        elapsed = datetime.datetime.now(
            datetime.timezone.utc
        ) - dateparser.parse(str(proxy.created))
        if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
            delete_proxy(proxy)
            logger.info(
                "Recycling proxy, reached age limit -> " + str(proxy.public_net.ipv4.ip)
            )
        elif check_alive(proxy.public_net.ipv4.ip):
            logger.info("Alive: Hetzner -> " + str(proxy.public_net.ipv4.ip))
            ip_ready.append(proxy.public_net.ipv4.ip)
        else:
            if elapsed > datetime.timedelta(minutes=10):
                delete_proxy(proxy)
                logger.info(
                    "Destroyed: Hetzner took too long -> " + str(proxy.public_net.ipv4.ip)
                )
            else:
                logger.info("Waiting: Hetzner -> " + str(proxy.public_net.ipv4.ip))
    return ip_ready


def hetzner_check_delete():
    for proxy in list_proxies():
        if proxy.public_net.ipv4.ip in delete_queue or proxy.public_net.ipv4.ip in restart_queue:
            delete_proxy(proxy)
            logger.info("Destroyed: not wanted -> " + str(proxy.public_net.ipv4.ip))
            delete_queue.remove(proxy.public_net.ipv4.ip)


def hetzner_start():
    hetzner_check_delete()
    hetzner_deployment(settings.config["providers"]["hetzner"]["scaling"]["min_scaling"])
    ip_ready = hetzner_check_alive()
    return ip_ready
