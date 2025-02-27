import pytest
from cloudproxy.providers.digitalocean.functions import create_proxy, delete_proxy, list_droplets, get_manager
import os
import json
from unittest.mock import MagicMock, patch
from cloudproxy.providers import settings


class Droplet:
    def __init__(self, id):
        self.id = id
        self.tags = ["cloudproxy"]


def load_from_file(json_file):
    cwd = os.path.dirname(__file__)
    with open(os.path.join(cwd, json_file), 'r') as f:
        return json.loads(f.read())


@pytest.fixture
def droplets(mocker):
    """Fixture for droplets data."""
    data = load_from_file('test_providers_digitalocean_functions_droplets_all.json')
    # Convert the dictionary droplets to Droplet objects
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
def instance_specific_droplets(mocker):
    """Fixture for instance-specific droplets data."""
    # Create droplets with instance-specific tags
    droplet_objects = []
    
    # Default instance droplets
    default_droplet1 = Droplet(1001)
    default_droplet1.tags = ["cloudproxy", "cloudproxy-default"]
    droplet_objects.append(default_droplet1)
    
    default_droplet2 = Droplet(1002)
    default_droplet2.tags = ["cloudproxy", "cloudproxy-default"]
    droplet_objects.append(default_droplet2)
    
    # Instance "useast" droplets
    useast_droplet1 = Droplet(2001)
    useast_droplet1.tags = ["cloudproxy", "cloudproxy-useast"]
    droplet_objects.append(useast_droplet1)
    
    useast_droplet2 = Droplet(2002)
    useast_droplet2.tags = ["cloudproxy", "cloudproxy-useast"]
    droplet_objects.append(useast_droplet2)
    
    # Old-style droplets without instance tag
    old_droplet = Droplet(3001)
    old_droplet.tags = ["cloudproxy"]
    droplet_objects.append(old_droplet)
    
    return droplet_objects


@pytest.fixture
def test_instance_config():
    """Fixture for a test instance configuration."""
    return {
        "enabled": True,
        "secrets": {
            "access_token": "test-token-useast"
        },
        "size": "s-1vcpu-1gb",
        "region": "nyc1",
        "min_scaling": 2,
        "max_scaling": 5,
        "display_name": "US East"
    }


@pytest.fixture
def droplet_id():
    """Fixture for droplet ID."""
    return "DROPLET-ID"


@patch('cloudproxy.providers.digitalocean.functions.get_manager')
def test_list_droplets(mock_get_manager):
    """Test listing droplets."""
    # Setup
    mock_manager = MagicMock()
    mock_get_manager.return_value = mock_manager
    
    mock_droplets = [MagicMock(id=i) for i in range(1, 5)]
    mock_manager.get_all_droplets.return_value = mock_droplets
    
    # Execute
    with patch('cloudproxy.providers.digitalocean.functions.settings.config', {
        "providers": {
            "digitalocean": {
                "instances": {
                    "default": {
                        "secrets": {
                            "access_token": "test-token"
                        }
                    }
                }
            }
        }
    }):
        result = list_droplets()
    
    # Verify
    assert mock_get_manager.called
    mock_manager.get_all_droplets.assert_called()
    assert isinstance(result, list)
    assert len(result) == 4
    assert result == mock_droplets


@patch('cloudproxy.providers.digitalocean.functions.get_manager')
@patch('cloudproxy.providers.digitalocean.functions.set_auth')
def test_create_proxy(mock_set_auth, mock_get_manager):
    """Test creating a proxy."""
    # Setup
    mock_set_auth.return_value = "mocked-user-data"
    mock_manager = MagicMock()
    mock_get_manager.return_value = mock_manager
    
    mock_droplet = MagicMock()
    mock_manager.get_droplet.return_value = mock_droplet
    
    # Execute
    with patch('cloudproxy.providers.digitalocean.functions.digitalocean.Droplet.create') as mock_create, \
         patch('cloudproxy.providers.digitalocean.functions.settings.config', {
             "providers": {
                 "digitalocean": {
                     "instances": {
                         "default": {
                             "secrets": {
                                 "access_token": "test-token"
                             },
                             "region": "nyc1",
                             "size": "s-1vcpu-1gb"
                         }
                     }
                 }
             },
             "auth": {
                 "username": "test-user",
                 "password": "test-pass"
             }
         }), \
         patch('cloudproxy.providers.digitalocean.functions.uuid.uuid1', return_value="test-uuid"):
        mock_create.return_value = True
        result = create_proxy()
    
    # Verify
    assert mock_get_manager.called
    assert mock_create.called
    assert result is True


def test_delete_proxy():
    """Test that we can delete a proxy."""
    # Mock digitalocean.Droplet directly
    with patch('cloudproxy.providers.digitalocean.functions.get_manager') as mock_get_manager, \
         patch('cloudproxy.providers.digitalocean.functions.settings.config', {
             "providers": {
                 "digitalocean": {
                     "instances": {
                         "default": {
                             "secrets": {
                                 "access_token": "test-token"
                             }
                         }
                     }
                 }
             }
         }):
        # Setup
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager
        
        mock_droplet = MagicMock()
        mock_manager.get_droplet.return_value = mock_droplet
        mock_droplet.destroy.return_value = True
        
        # Execute
        result = delete_proxy(1)
        
        # Verify
        assert mock_get_manager.called
        mock_manager.get_droplet.assert_called_once_with(1)
        mock_droplet.destroy.assert_called_once()
        assert result is True


@patch('cloudproxy.providers.digitalocean.functions.get_manager')
def test_delete_proxy_with_instance_config(mock_get_manager, test_instance_config):
    """Test that we can delete a proxy with a specific instance configuration."""
    # Setup
    mock_manager = MagicMock()
    mock_get_manager.return_value = mock_manager
    
    mock_droplet = MagicMock()
    mock_manager.get_droplet.return_value = mock_droplet
    mock_droplet.destroy.return_value = True
    
    # Execute
    result = delete_proxy(1, test_instance_config)
    
    # Verify
    mock_get_manager.assert_called_once_with(test_instance_config)
    mock_manager.get_droplet.assert_called_once_with(1)
    mock_droplet.destroy.assert_called_once()
    assert result is True


@patch('cloudproxy.providers.digitalocean.functions.digitalocean.Manager')
def test_get_manager_default(mock_manager):
    """Test get_manager with default configuration."""
    # Setup
    mock_manager_instance = MagicMock()
    mock_manager.return_value = mock_manager_instance
    
    # Mock settings to ensure access_token is available
    test_config = {
        "providers": {
            "digitalocean": {
                "instances": {
                    "default": {
                        "secrets": {
                            "access_token": "test-token"
                        }
                    }
                }
            }
        }
    }
    
    with patch('cloudproxy.providers.digitalocean.functions.settings.config', test_config):
        # Call function under test
        result = get_manager()
    
    # Verify
    mock_manager.assert_called_once_with(token="test-token")
    assert result == mock_manager_instance


@patch('cloudproxy.providers.digitalocean.functions.digitalocean.Manager')
def test_get_manager_with_instance_config(mock_manager, test_instance_config):
    """Test get_manager with a specific instance configuration."""
    # Setup mock
    mock_manager_instance = MagicMock()
    mock_manager.return_value = mock_manager_instance
    
    # Call function under test
    result = get_manager(test_instance_config)
    
    # Verify
    mock_manager.assert_called_once()
    assert mock_manager.call_args[1]['token'] == "test-token-useast"
    assert result == mock_manager_instance


@patch('cloudproxy.providers.digitalocean.functions.digitalocean.Droplet')
def test_create_proxy_with_instance_config(mock_droplet, test_instance_config):
    """Test creating a proxy with a specific instance configuration."""
    # Setup mock
    mock_droplet_instance = MagicMock()
    mock_droplet.return_value = mock_droplet_instance
    
    # Save the original config to restore later
    original_config = settings.config["providers"]["digitalocean"]["instances"].copy()
    
    # Add our test instance config
    settings.config["providers"]["digitalocean"]["instances"]["useast"] = test_instance_config
    
    try:
        # Call function under test
        result = create_proxy(test_instance_config)
        
        # Verify
        mock_droplet.assert_called_once()
        args, kwargs = mock_droplet.call_args
        
        # Verify token, region, and size from instance config were used
        assert kwargs['token'] == "test-token-useast"
        assert kwargs['region'] == "nyc1"
        assert kwargs['size_slug'] == "s-1vcpu-1gb"
        
        # Verify that correct tags are set
        assert "cloudproxy" in kwargs['tags']
        assert "cloudproxy-useast" in kwargs['tags']
        
        # Verify name format includes instance identifier
        assert "cloudproxy-useast-" in kwargs['name']
        
        assert result == True
    finally:
        # Restore original config
        settings.config["providers"]["digitalocean"]["instances"] = original_config


@patch('cloudproxy.providers.digitalocean.functions.get_manager')
def test_list_droplets_with_instance_config_default(mock_get_manager, instance_specific_droplets):
    """Test listing droplets using the default instance configuration."""
    # Setup mock
    mock_manager = MagicMock()
    mock_get_manager.return_value = mock_manager
    
    # First call returns droplets with instance tag
    # Create a copy of the droplets with cloudproxy-default tag to return from the first call
    default_droplets = [d for d in instance_specific_droplets if "cloudproxy-default" in d.tags]
    
    # Second call returns all cloudproxy droplets for filtering old ones
    all_droplets = instance_specific_droplets.copy()
    
    # Configure get_all_droplets mock to return different values on each call
    mock_manager.get_all_droplets.side_effect = [default_droplets, all_droplets]
    
    # Call function under test
    result = list_droplets()  # Default instance
    
    # Verify
    assert mock_manager.get_all_droplets.call_count == 2
    
    # Check that the first call used the right tag_name
    assert mock_manager.get_all_droplets.call_args_list[0][1]['tag_name'] == 'cloudproxy-default'
    
    # Check that the second call used the right tag_name 
    assert mock_manager.get_all_droplets.call_args_list[1][1]['tag_name'] == 'cloudproxy'
    
    # Match droplet ids instead of just comparing length
    old_droplets = [d for d in all_droplets if len(d.tags) == 1 and "cloudproxy" in d.tags]
    
    expected_ids = set()
    for droplet in default_droplets:
        expected_ids.add(droplet.id)
    for droplet in old_droplets:
        expected_ids.add(droplet.id)
        
    result_ids = set(droplet.id for droplet in result)
    assert result_ids == expected_ids


@patch('cloudproxy.providers.digitalocean.functions.get_manager')
def test_list_droplets_with_instance_config_specific(mock_get_manager, instance_specific_droplets, test_instance_config):
    """Test listing droplets using a specific instance configuration."""
    # Setup mock
    mock_manager = MagicMock()
    mock_get_manager.return_value = mock_manager
    
    # Setup specific instance droplets
    useast_droplets = [d for d in instance_specific_droplets if 'cloudproxy-useast' in d.tags]
    mock_manager.get_all_droplets.return_value = useast_droplets
    
    # Save the original config to restore later
    original_config = settings.config["providers"]["digitalocean"]["instances"].copy()
    
    # Add our test instance config
    settings.config["providers"]["digitalocean"]["instances"]["useast"] = test_instance_config
    
    try:
        # Call function under test
        result = list_droplets(test_instance_config)
        
        # Verify
        mock_manager.get_all_droplets.assert_called_once_with(tag_name='cloudproxy-useast')
        
        # Should include only the specific instance's droplets
        assert len(result) == len(useast_droplets)
        result_ids = [d.id for d in result]
        
        # Check for useast instance droplets
        assert 2001 in result_ids
        assert 2002 in result_ids
        
        # Should NOT include other instances' droplets
        assert 1001 not in result_ids
        assert 1002 not in result_ids
        assert 3001 not in result_ids
    finally:
        # Restore original config
        settings.config["providers"]["digitalocean"]["instances"] = original_config
