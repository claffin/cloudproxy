import os

import digitalocean
import uuid as uuid

from cloudproxy.check import check_alive
from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth

manager = digitalocean.Manager(
    token=settings.config["providers"]["digitalocean"]["secrets"]["access_token"]
)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

token = settings.config["providers"]["digitalocean"]["secrets"]["access_token"]



def create_proxy():
    user_data = set_auth(
        settings.config["auth"]["username"], settings.config["auth"]["password"]
    )
    digitalocean.Droplet(
        name=str(uuid.uuid1()),
        region=settings.config["providers"]["digitalocean"]["region"],
        image="ubuntu-20-04-x64",
        size_slug=settings.config["providers"]["digitalocean"]["size"],
        backups=False,
        user_data=user_data,
        tags="cloudproxy",
    ).create()
    return True


def delete_proxy(droplet_id):
    deleted = digitalocean.Droplet.destroy(droplet_id)
    return deleted


def list_droplets():
    my_droplets = manager.get_all_droplets(tag_name="cloudproxy")
    return my_droplets
