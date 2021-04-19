from apscheduler.schedulers.background import BackgroundScheduler

from cloudproxy.providers import settings
from cloudproxy.providers.settings import username, password
from cloudproxy.providers.digitalocean.main import initatedo


def returnips():
    ip_list = initatedo()
    settings.ip_list = ["http://" + username + ":" + password + "@" + ip + ":8899" for ip in ip_list]


def init_schedule():
    sched = BackgroundScheduler()
    sched.start()
    sched.add_job(returnips, 'interval', seconds=30)
