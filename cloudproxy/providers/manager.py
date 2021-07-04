from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from cloudproxy.providers import settings
from cloudproxy.providers.aws.main import aws_start
from cloudproxy.providers.gcp.main import gcp_start
from cloudproxy.providers.digitalocean.main import do_start
from cloudproxy.providers.hetzner.main import hetzner_start


def do_manager():
    ip_list = do_start()
    settings.config["providers"]["digitalocean"]["ips"] = [ip for ip in ip_list]
    return ip_list

def aws_manager():
    ip_list = aws_start()
    settings.config["providers"]["aws"]["ips"] = [ip for ip in ip_list]
    return ip_list

def gcp_manager():
    ip_list = gcp_start()
    settings.config["providers"]["gcp"]["ips"] = [ip for ip in ip_list]
    return ip_list

def hetzner_manager():
    ip_list = hetzner_start()
    settings.config["providers"]["hetzner"]["ips"] = [ip for ip in ip_list]
    return ip_list


def init_schedule():
    sched = BackgroundScheduler()
    sched.start()
    if settings.config["providers"]["digitalocean"]["enabled"] == 'True':
        sched.add_job(do_manager, "interval", seconds=20)
    else:
        logger.info("DigitalOcean not enabled")
    if settings.config["providers"]["aws"]["enabled"] == 'True':
        sched.add_job(aws_manager, "interval", seconds=20)
    else:
        logger.info("AWS not enabled")
    if settings.config["providers"]["gcp"]["enabled"] == 'True':
        sched.add_job(gcp_manager, "interval", seconds=20)
    else:
        logger.info("GCP not enabled")
    if settings.config["providers"]["hetzner"]["enabled"] == 'True':
        sched.add_job(hetzner_manager, "interval", seconds=20)
    else:
        logger.info("Hetzner not enabled")
