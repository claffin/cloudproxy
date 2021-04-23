from apscheduler.schedulers.background import BackgroundScheduler
from loguru import logger
from cloudproxy.providers import settings
from cloudproxy.providers.aws.main import aws_start
from cloudproxy.providers.digitalocean.main import do_start


def do_manager():
    ip_list = do_start()
    settings.config["providers"]["digitalocean"]["ips"] = [
        "http://"
        + settings.config["auth"]["username"]
        + ":"
        + settings.config["auth"]["password"]
        + "@"
        + ip
        + ":8899"
        for ip in ip_list
    ]
    return ip_list


def aws_manager():
    ip_list = aws_start()
    settings.config["providers"]["aws"]["ips"] = [
        "http://"
        + settings.config["auth"]["username"]
        + ":"
        + settings.config["auth"]["password"]
        + "@"
        + ip
        + ":8899"
        for ip in ip_list
    ]
    return ip_list


def init_schedule():
    sched = BackgroundScheduler()
    sched.start()
    if settings.config["providers"]["digitalocean"]["enabled"]:
        sched.add_job(do_manager, "interval", seconds=30)
    else:
        logger.info("DigitalOcean not enabled")
    if settings.config["providers"]["aws"]["enabled"]:
        sched.add_job(aws_manager, "interval", seconds=30)
    else:
        logger.info("AWS not enabled")
