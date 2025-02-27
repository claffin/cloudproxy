import pytest
from cloudproxy.providers.digitalocean.main import do_deployment, do_start
from cloudproxy.providers.digitalocean.functions import list_droplets, delete_proxy
from tests.test_providers_digitalocean_functions import load_from_file


@pytest.fixture
def droplets(mocker):
    """Fixture for droplets data."""
    data = load_from_file('test_providers_digitalocean_functions_droplets_all.json')
    # Convert the dictionary droplets to Droplet objects
    from tests.test_providers_digitalocean_functions import Droplet
    droplet_objects = []
    for droplet_dict in data['droplets']:
        droplet = Droplet(droplet_dict['id'])
        # Add tags attribute to the droplet
        droplet.tags = ["cloudproxy"]
        droplet_objects.append(droplet)
    
    mocker.patch('cloudproxy.providers.digitalocean.functions.digitalocean.Manager.get_all_droplets',
                 return_value=droplet_objects)
    return droplet_objects


@pytest.fixture
def droplet_id():
    """Fixture for droplet ID."""
    return "DROPLET-ID"


def test_do_deployment(mocker, droplets, droplet_id):
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.list_droplets',
        return_value=droplets
    )
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.create_proxy',
        return_value=True
    )
    mocker.patch(
        'cloudproxy.providers.digitalocean.main.delete_proxy',
        return_value=True
    )
    result = do_deployment(1)
    assert isinstance(result, int)
    assert result == 1


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
        'cloudproxy.providers.digitalocean.main.do_check_delete',
        return_value=True
    )
    result = do_start()
    assert isinstance(result, list)
    assert result == ["192.1.1.1"]


def test_list_droplets(droplets):
    """Test listing droplets."""
    result = list_droplets()
    assert isinstance(result, list)
    assert len(result) > 0
    assert result[0].id == 3164444  # Verify specific droplet data
    # Store the result in a module-level variable if needed by other tests
    global test_droplets
    test_droplets = result


def test_delete_proxy(mocker, droplets):
    """Test deleting a proxy."""
    assert len(droplets) > 0
    droplet_id = droplets[0].id
    
    # Mock the Manager and get_droplet method to avoid real API calls
    mock_manager = mocker.patch('cloudproxy.providers.digitalocean.functions.get_manager')
    mock_manager_instance = mocker.MagicMock()
    mock_manager.return_value = mock_manager_instance
    
    # Mock the droplet that will be returned by get_droplet
    mock_droplet = mocker.MagicMock()
    mock_droplet.destroy.return_value = True
    mock_manager_instance.get_droplet.return_value = mock_droplet
    
    # Test the delete_proxy function
    assert delete_proxy(droplet_id) == True
    
    # Verify our mock was called correctly
    mock_manager.assert_called_once()
    mock_manager_instance.get_droplet.assert_called_once_with(droplet_id)
    mock_droplet.destroy.assert_called_once()