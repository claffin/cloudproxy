import datetime
import itertools

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.digitalocean.functions import create_proxy, list_droplets, delete_proxy
from cloudproxy.providers import settings
from cloudproxy.providers.settings import delete_queue


def do_deployment(min_scaling):
    total_droplets = len(list_droplets())
    if min_scaling < total_droplets:
        logger.info("Overprovisioned: DO destroying.....")
        for droplet in itertools.islice(list_droplets(), 0, (total_droplets - min_scaling)):
            delete_proxy(droplet)
            logger.info("Destroyed: DO -> " + str(droplet.ip_address))
    if min_scaling - total_droplets < 1:
        logger.info("Minimum DO Droplets met")
    else:
        total_deploy = min_scaling - total_droplets
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


def check_delete():
    for droplet in list_droplets():
        if droplet.ip_address in delete_queue:
            delete_proxy(droplet)
            logger.info("Destroyed: not wanted -> " + str(droplet.ip_address))
            delete_queue.remove(droplet.ip_address)
            return True
        else:
            return False


def initiatedo():
    do_deployment(settings.config["providers"]["digitalocean"]["scaling"]["min_scaling"])
    ip_ready = do_check_alive()
    check_delete()
    return ip_ready
