from cloudproxy.providers.digitalocean.functions import create_proxy, delete_proxy, list_droplets


def test_create_proxy():
    assert create_proxy() is not None


def test_list_droplets():
    assert type(list_droplets()) is list


def test_delete_proxy():
    droplet_id = list_droplets()[0]
    assert delete_proxy(droplet_id) == True
