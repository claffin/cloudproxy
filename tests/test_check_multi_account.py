import pytest
from unittest.mock import patch, MagicMock
import requests

from cloudproxy.check import check_alive, fetch_ip
from cloudproxy.providers import settings


@pytest.fixture
def mock_proxy_data():
    """Fixture for mock proxy data from different provider instances."""
    return [
        {
            "ip": "192.168.1.10",
            "provider": "digitalocean",
            "instance": "default",
            "display_name": "London DO"
        },
        {
            "ip": "192.168.1.20",
            "provider": "digitalocean",
            "instance": "nyc",
            "display_name": "New York DO"
        },
        {
            "ip": "192.168.1.30",
            "provider": "aws",
            "instance": "default",
            "display_name": "US East AWS"
        },
        {
            "ip": "192.168.1.40",
            "provider": "aws",
            "instance": "eu",
            "display_name": "EU West AWS"
        },
        {
            "ip": "192.168.1.50",
            "provider": "hetzner",
            "instance": "default",
            "display_name": "Germany Hetzner"
        }
    ]


@pytest.fixture(autouse=True)
def setup_auth():
    """Setup authentication for all tests."""
    # Save original config
    original_auth = settings.config.get("auth", {}).copy() if "auth" in settings.config else {}
    original_no_auth = settings.config.get("no_auth", True)
    
    # Set test credentials
    settings.config["auth"] = {
        "username": "testuser",
        "password": "testpass"
    }
    settings.config["no_auth"] = False
    
    yield
    
    # Restore original config
    settings.config["auth"] = original_auth
    settings.config["no_auth"] = original_no_auth


@patch('cloudproxy.check.requests.get')
def test_check_alive_for_different_instances(mock_requests_get, mock_proxy_data):
    """Test check_alive function for proxies from different provider instances."""
    # Setup mock response with success status code
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response
    
    # Set no_auth to True
    original_no_auth = settings.config["no_auth"]
    settings.config["no_auth"] = True
    try:
        # Test check_alive for each proxy
        for proxy in mock_proxy_data:
            # Call function under test
            result = check_alive(proxy["ip"])
            # Verify result
            assert result is True, f"check_alive for {proxy['ip']} from {proxy['provider']}/{proxy['instance']} should return True"
            # Verify correct proxy was used in the request
            expected_proxy = {'http': f'http://{proxy["ip"]}:8899', 'https': f'http://{proxy["ip"]}:8899'}
            mock_requests_get.assert_called_with(
                "http://ipecho.net/plain", 
                proxies=expected_proxy, 
                timeout=10
            )
            # Reset mock for next iteration
            mock_requests_get.reset_mock()
    finally:
        settings.config["no_auth"] = original_no_auth


@patch('cloudproxy.check.requests_retry_session')
def test_fetch_ip_with_auth_for_different_instances(mock_retry_session, mock_proxy_data):
    """Test fetch_ip function with authentication for proxies from different provider instances."""
    # Disable no_auth
    settings.config["no_auth"] = False
    
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "mocked-ip-response"
    
    # Setup mock session
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_retry_session.return_value = mock_session
    
    # Test fetch_ip for each proxy
    for proxy in mock_proxy_data:
        # Call function under test
        result = fetch_ip(proxy["ip"])
        
        # Verify result
        assert result == "mocked-ip-response", f"fetch_ip for {proxy['ip']} from {proxy['provider']}/{proxy['instance']} returned unexpected value"
        
        # Verify correct proxies were used in the request
        expected_proxies = {
            'http': f'http://testuser:testpass@{proxy["ip"]}:8899',
            'https': f'http://testuser:testpass@{proxy["ip"]}:8899'
        }
        mock_session.get.assert_called_with(
            "https://api.ipify.org",
            proxies=expected_proxies,
            timeout=10
        )
        
        # Reset mocks for next iteration
        mock_session.reset_mock()
        mock_retry_session.reset_mock()


@patch('cloudproxy.check.requests_retry_session')
def test_fetch_ip_without_auth_for_different_instances(mock_retry_session, mock_proxy_data):
    """Test fetch_ip function without authentication for proxies from different provider instances."""
    # Enable no_auth
    settings.config["no_auth"] = True
    
    # Setup mock response
    mock_response = MagicMock()
    mock_response.text = "mocked-ip-response"
    
    # Setup mock session
    mock_session = MagicMock()
    mock_session.get.return_value = mock_response
    mock_retry_session.return_value = mock_session
    
    # Test fetch_ip for each proxy
    for proxy in mock_proxy_data:
        # Call function under test
        result = fetch_ip(proxy["ip"])
        
        # Verify result
        assert result == "mocked-ip-response", f"fetch_ip for {proxy['ip']} from {proxy['provider']}/{proxy['instance']} returned unexpected value"
        
        # Verify correct proxies were used in the request
        expected_proxies = {
            'http': f'http://{proxy["ip"]}:8899',
            'https': f'http://{proxy["ip"]}:8899'
        }
        mock_session.get.assert_called_with(
            "https://api.ipify.org",
            proxies=expected_proxies,
            timeout=10
        )
        
        # Reset mocks for next iteration
        mock_session.reset_mock()
        mock_retry_session.reset_mock()


@patch('cloudproxy.check.requests.get')
def test_check_alive_exception_handling_for_different_instances(mock_get, mock_proxy_data):
    """Test that check_alive properly handles exceptions for proxies from different provider instances."""
    # List of exceptions to test
    exceptions = [
        requests.exceptions.ConnectTimeout("Connection timed out"),
        requests.exceptions.ConnectionError("Connection refused"),
        requests.exceptions.ReadTimeout("Read timed out"),
        requests.exceptions.ProxyError("Proxy error")
    ]
    
    # Last proxy in the list will work
    last_proxy = mock_proxy_data[-1]
    
    # Test each proxy
    for i, proxy in enumerate(mock_proxy_data):
        if i < len(mock_proxy_data) - 1:
            # Configure exception for proxies except the last one
            mock_get.side_effect = exceptions[i % len(exceptions)]
        else:
            # Configure success for the last proxy
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.side_effect = None
            mock_get.return_value = mock_response
        
        # Call function under test
        result = check_alive(proxy["ip"])
        
        # Verify result
        if proxy["ip"] == last_proxy["ip"]:
            assert result is True, f"Proxy {proxy['ip']} should be alive"
        else:
            assert result is False, f"Proxy {proxy['ip']} should handle exception and return False"
        
        # Reset mock for next iteration
        mock_get.reset_mock() 