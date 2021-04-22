from apscheduler.schedulers.background import BackgroundScheduler

from cloudproxy.providers import settings
from cloudproxy.providers.digitalocean.main import initiatedo


def returnips():
    ip_list = initiatedo()
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


def init_schedule():
    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(returnips, "interval", seconds=30)
