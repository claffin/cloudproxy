import os
import uuid

from hcloud import Client
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType
from hcloud.datacenters.domain import Datacenter
from hcloud.locations.domain import Location

from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth

client = Client(token=settings.config["providers"]["hetzner"]["secrets"]["access_token"])
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def create_proxy():
    user_data = set_auth(
        settings.config["auth"]["username"], settings.config["auth"]["password"]
    )
    client.servers.create(name=str(uuid.uuid1()),
                          server_type=ServerType("cx11"),
                          image=Image(name="ubuntu-20.04"),
                          location=Location(name=settings.config["providers"]["hetzner"]["location"]),
                          # datacenter=Datacenter(name=settings.config["providers"]["hetzner"]["datacenter"]),
                          user_data=user_data, labels={"cloudproxy": "cloudproxy"})
    return True


def delete_proxy(server):
    deleted = client.servers.delete(server)
    return deleted


def list_proxies():
    servers = client.servers.get_all(label_selector={"cloudproxy": "cloudproxy"})
    return servers
