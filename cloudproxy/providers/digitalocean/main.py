import datetime
import itertools

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.digitalocean.functions import create_proxy, list_droplets, delete_proxy
from cloudproxy.providers.settings import min_scaling


def do_deployment():
    total_droplets = len(list_droplets())
    if int(min_scaling) < total_droplets:
        logger.info("Overprovisioned: DO destroying.....")
        for droplet in itertools.islice(list_droplets(), 0, (total_droplets - int(min_scaling))):
            delete_proxy(droplet)
            logger.info("Destroyed: DO -> " + str(droplet.ip_address))
    if int(min_scaling) - total_droplets < 1:
        logger.info("Minimum DO Droplets met")
    else:
        total_deploy = int(min_scaling) - total_droplets
        logger.info("Deploying: " + str(total_deploy) + " DO droplets")
        for _ in range(total_deploy):
            create_proxy()
            logger.info("Deployed")
    return len(list_droplets())


def do_check_alive():
    ip_ready = []
    for droplet in list_droplets():
        try:
            if check_alive(droplet.ip_address):
                logger.info("Alive: DO -> " + str(droplet.ip_address))
                ip_ready.append(droplet.ip_address)
            else:
                elapsed = datetime.datetime.now(datetime.timezone.utc) - dateparser.parse(droplet.created_at)
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(droplet)
                    logger.info("Destroyed: took too long DO -> " + str(droplet.ip_address))
                else:
                    logger.info("Waiting: DO -> " + str(droplet.ip_address))
        except TypeError:
            logger.info("Pending: DO allocating")
    return ip_ready


def initatedo():
    do_deployment()
    ip_ready = do_check_alive()
    return ip_ready
