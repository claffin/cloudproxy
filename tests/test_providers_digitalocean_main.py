from cloudproxy.providers.digitalocean.main import do_deployment, do_check_alive
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