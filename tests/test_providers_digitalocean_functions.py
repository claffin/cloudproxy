import pytest
from cloudproxy.providers.digitalocean.functions import create_proxy, delete_proxy, list_droplets
import os
import json


class Droplet:
    def __init__(self, id):
        self.id = id


def load_from_file(json_file):
    cwd = os.path.dirname(__file__)
    with open(os.path.join(cwd, json_file), 'r') as f:
        return json.loads(f.read())


@pytest.fixture
def droplets(mocker):
    """Fixture for droplets data."""
    data = load_from_file('test_providers_digitalocean_functions_droplets_all.json')
    mocker.patch('cloudproxy.providers.digitalocean.functions.digitalocean.Manager.get_all_droplets',
                 return_value=data['droplets'])
    return data['droplets']


@pytest.fixture
def droplet_id():
    """Fixture for droplet ID."""
    return "DROPLET-ID"


def test_list_droplets(droplets):
    """Test listing droplets."""
    result = list_droplets()
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0]['id'] == 3164444  # Verify specific droplet data


def test_create_proxy(mocker, droplet_id):
    """Test creating a proxy."""
    droplet = Droplet(droplet_id)
    mocker.patch(
        'cloudproxy.providers.digitalocean.functions.digitalocean.Droplet.create',
        return_value=droplet
    )
    assert create_proxy() == True


def test_delete_proxy(mocker, droplets):
    """Test deleting a proxy."""
    assert len(droplets) > 0
    droplet_id = droplets[0]['id']
    mocker.patch(
        'cloudproxy.providers.digitalocean.functions.digitalocean.Droplet.destroy',
        return_value=True
    )
    assert delete_proxy(droplet_id) == True
