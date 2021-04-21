from cloudproxy.providers.digitalocean.functions import create_proxy, delete_proxy, list_droplets
import os
import json


class Droplet:
    def __init__(self, id):
        self.id = id


def test_create_proxy(mocker):
    droplet = Droplet("DROPLET-ID")
    mocker.patch(
        'cloudproxy.providers.digitalocean.functions.digitalocean.Droplet.create',
        return_value=droplet
    )
    assert create_proxy() == True


def test_delete_proxy(mocker):
    droplet_id = test_list_droplets(mocker)[0]
    mocker.patch(
        'cloudproxy.providers.digitalocean.functions.digitalocean.Droplet.destroy',
        return_value=True
    )
    assert delete_proxy(droplet_id) == True


def test_list_droplets(mocker):
    droplets = load_from_file('test_providers_digitalocean_functions_droplets_all.json')
    mocker.patch('cloudproxy.providers.digitalocean.functions.digitalocean.Manager.get_all_droplets',
                 return_value=droplets['droplets'])
    assert type(list_droplets()) is list
    return list_droplets()


def load_from_file(json_file):
    cwd = os.path.dirname(__file__)
    with open(os.path.join(cwd, json_file), 'r') as f:
        return json.loads(f.read())
