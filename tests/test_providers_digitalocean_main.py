from cloudproxy.providers.digitalocean.main import do_deployment, do_check_alive, initiatedo
from tests.test_providers_digitalocean_functions import test_list_droplets, test_create_proxy, test_delete_proxy


def test_do_deployment(mocker):
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.list_droplets',
        return_value=test_list_droplets(mocker)
    )
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.create_proxy',
        return_value=test_create_proxy(mocker)
    )
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.delete_proxy',
        return_value=test_delete_proxy(mocker)
    )
    assert do_deployment(1) == 1


def test_initiatedo(mocker):
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.do_deployment',
        return_value=2
    )
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.do_check_alive',
        return_value=["192.1.1.1"]
    )
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.check_delete',
        return_value=True
    )
    assert initiatedo() == ["192.1.1.1"]