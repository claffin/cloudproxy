import pytest
from unittest.mock import MagicMock, patch, Mock
from cloudproxy.providers.hetzner.functions import (
    get_client, create_proxy, delete_proxy, list_proxies
)
from cloudproxy.providers import settings


@pytest.fixture
def mock_server():
    """Create a mock server instance."""
    server = Mock()
    server.id = "server-id-1"
    server.name = "cloudproxy-default-uuid1"
    server.labels = {"type": "cloudproxy", "instance": "default"}
    return server


@pytest.fixture
def mock_servers():
    """Create a list of mock servers."""
    servers = []
    
    # Default instance servers
    server1 = Mock()
    server1.id = "server-id-1"
    server1.name = "cloudproxy-default-uuid1"
    server1.labels = {"type": "cloudproxy", "instance": "default"}
    servers.append(server1)
    
    server2 = Mock()
    server2.id = "server-id-2"
    server2.name = "cloudproxy-default-uuid2"
    server2.labels = {"type": "cloudproxy", "instance": "default"}
    servers.append(server2)
    
    # Custom instance servers
    server3 = Mock()
    server3.id = "server-id-3"
    server3.name = "cloudproxy-europe-uuid3"
    server3.labels = {"type": "cloudproxy", "instance": "europe"}
    servers.append(server3)
    
    server4 = Mock()
    server4.id = "server-id-4"
    server4.name = "cloudproxy-europe-uuid4"
    server4.labels = {"type": "cloudproxy", "instance": "europe"}
    servers.append(server4)
    
    # Old-style server without instance label
    server5 = Mock()
    server5.id = "server-id-5"
    server5.name = "cloudproxy-uuid5"
    server5.labels = {"type": "cloudproxy"}
    servers.append(server5)
    
    return servers


@pytest.fixture
def test_instance_config():
    """Fixture for a test instance configuration."""
    return {
        "enabled": True,
        "secrets": {
            "access_token": "europe-test-token"
        },
        "size": "cx11",
        "location": "hel1",
        "min_scaling": 2,
        "max_scaling": 5,
        "display_name": "Europe Hetzner"
    }


@patch('cloudproxy.providers.hetzner.functions.Client')
def test_get_client_default(mock_client):
    """Test get_client with default configuration."""
    # Setup
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Execute
    result = get_client()
    
    # Verify
    mock_client.assert_called_once_with(
        token=settings.config["providers"]["hetzner"]["instances"]["default"]["secrets"]["access_token"]
    )
    assert result == mock_client_instance


@patch('cloudproxy.providers.hetzner.functions.Client')
def test_get_client_with_instance_config(mock_client, test_instance_config):
    """Test get_client with a specific instance configuration."""
    # Setup
    mock_client_instance = MagicMock()
    mock_client.return_value = mock_client_instance
    
    # Execute
    result = get_client(test_instance_config)
    
    # Verify
    mock_client.assert_called_once_with(token="europe-test-token")
    assert result == mock_client_instance


@patch('cloudproxy.providers.hetzner.functions.get_client')
@patch('cloudproxy.providers.hetzner.functions.set_auth')
@patch('cloudproxy.providers.hetzner.functions.uuid')
def test_create_proxy_default(mock_uuid, mock_set_auth, mock_get_client):
    """Test create_proxy with default configuration."""
    # Setup
    mock_uuid.uuid4.return_value = "test-uuid"
    mock_set_auth.return_value = "user-data-script"
    
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_client.servers.create.return_value = mock_response
    
    # Execute
    result = create_proxy()
    
    # Verify
    assert mock_get_client.call_count == 1
    mock_client.servers.create.assert_called_once()
    assert "cloudproxy-default-test-uuid" in mock_client.servers.create.call_args[1]["name"]
    assert result == mock_response


@patch('cloudproxy.providers.hetzner.functions.get_client')
@patch('cloudproxy.providers.hetzner.functions.set_auth')
@patch('cloudproxy.providers.hetzner.functions.uuid')
def test_create_proxy_with_instance_config(mock_uuid, mock_set_auth, mock_get_client, test_instance_config):
    """Test create_proxy with a specific instance configuration."""
    # Setup
    mock_uuid.uuid4.return_value = "test-uuid"
    mock_set_auth.return_value = "user-data-script"
    
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_response = MagicMock()
    mock_client.servers.create.return_value = mock_response
    
    # Save the original config to restore later
    original_config = settings.config["providers"]["hetzner"]["instances"].copy()
    
    # Add our test instance config
    settings.config["providers"]["hetzner"]["instances"]["europe"] = test_instance_config
    
    try:
        # Execute
        result = create_proxy(test_instance_config)
        
        # Verify
        mock_get_client.assert_called_once_with(test_instance_config)
        mock_client.servers.create.assert_called_once()
        
        # Check server name format and configuration
        args, kwargs = mock_client.servers.create.call_args
        assert kwargs['name'] == "cloudproxy-europe-test-uuid"
        assert kwargs['labels'] == {"type": "cloudproxy", "instance": "europe"}
        
        # Check location is used from instance config
        assert kwargs['location'] is not None
        assert kwargs['location'].name == "hel1"
        
        assert result == mock_response
    finally:
        # Restore original config
        settings.config["providers"]["hetzner"]["instances"] = original_config


@patch('cloudproxy.providers.hetzner.functions.get_client')
def test_delete_proxy_default(mock_get_client, mock_server):
    """Test delete_proxy with default configuration."""
    # Setup
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_client.servers.get.return_value = mock_server
    mock_server.delete.return_value = "delete-response"
    
    # Execute
    result = delete_proxy("server-id-1")
    
    # Verify
    assert mock_get_client.call_count == 1
    mock_client.servers.get.assert_called_once_with("server-id-1")
    mock_server.delete.assert_called_once()
    assert result == "delete-response"


@patch('cloudproxy.providers.hetzner.functions.get_client')
def test_delete_proxy_with_instance_config(mock_get_client, mock_server, test_instance_config):
    """Test delete_proxy with a specific instance configuration."""
    # Setup
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    mock_client.servers.get.return_value = mock_server
    mock_server.delete.return_value = "delete-response"
    
    # Execute
    result = delete_proxy("server-id-1", test_instance_config)
    
    # Verify
    mock_get_client.assert_called_once_with(test_instance_config)
    mock_client.servers.get.assert_called_once_with("server-id-1")
    mock_server.delete.assert_called_once()
    assert result == "delete-response"


@patch('cloudproxy.providers.hetzner.functions.get_client')
def test_list_proxies_default(mock_get_client, mock_servers):
    """Test list_proxies with default configuration."""
    # Setup
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Filter mock servers for default instance first call
    default_servers = [s for s in mock_servers if "instance" in s.labels and s.labels["instance"] == "default"]
    # All servers with type=cloudproxy for second call
    type_servers = [s for s in mock_servers if "type" in s.labels and s.labels["type"] == "cloudproxy"]
    # Old-style servers for filtering
    old_servers = [s for s in type_servers if "instance" not in s.labels]
    
    mock_client.servers.get_all.side_effect = [default_servers, type_servers]
    
    # Execute
    result = list_proxies()
    
    # Verify
    assert mock_get_client.call_count == 1
    assert mock_client.servers.get_all.call_count == 2
    
    # First call should filter by label_selector for type=cloudproxy
    first_call_args = mock_client.servers.get_all.call_args_list[0]
    assert first_call_args[1]["label_selector"] == "type=cloudproxy"
    
    # Second call should also filter by type=cloudproxy
    second_call_args = mock_client.servers.get_all.call_args_list[1]
    assert second_call_args[1]["label_selector"] == "type=cloudproxy"
    
    # Check the result itself instead of just the length
    default_and_old_servers = set()
    for server in default_servers:
        default_and_old_servers.add(server.id)
    for server in old_servers:
        default_and_old_servers.add(server.id)
    
    result_ids = set(proxy.id for proxy in result)
    assert result_ids == default_and_old_servers


@patch('cloudproxy.providers.hetzner.functions.get_client')
def test_list_proxies_with_instance_config(mock_get_client, mock_servers, test_instance_config):
    """Test list_proxies with a specific instance configuration."""
    # Setup
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    
    # Filter mock servers for europe instance
    europe_servers = [s for s in mock_servers if "instance" in s.labels and s.labels["instance"] == "europe"]
    mock_client.servers.get_all.return_value = europe_servers
    
    # Save the original config to restore later
    original_config = settings.config["providers"]["hetzner"]["instances"].copy()
    
    # Add our test instance config
    settings.config["providers"]["hetzner"]["instances"]["europe"] = test_instance_config
    
    try:
        # Execute
        result = list_proxies(test_instance_config)
        
        # Verify
        mock_get_client.assert_called_once_with(test_instance_config)
        mock_client.servers.get_all.assert_called_once_with(label_selector="type=cloudproxy,instance=europe")
        
        # Result should only include europe instance servers
        assert len(result) == len(europe_servers)
        
        # Check specific server IDs
        result_ids = [s.id for s in result]
        # Europe instance servers
        assert "server-id-3" in result_ids
        assert "server-id-4" in result_ids
        # Default instance and old servers should NOT be included
        assert "server-id-1" not in result_ids
        assert "server-id-2" not in result_ids
        assert "server-id-5" not in result_ids
    finally:
        # Restore original config
        settings.config["providers"]["hetzner"]["instances"] = original_config 