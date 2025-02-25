import pytest
from unittest.mock import Mock, patch
import requests

from cloudproxy.check import requests_retry_session, fetch_ip, check_alive
from cloudproxy.providers import settings

@pytest.fixture
def mock_session():
    """Create a mock session for testing"""
    session = Mock(spec=requests.Session)
    session.mount = Mock()
    session.get = Mock()
    return session

def test_requests_retry_session_defaults():
    """Test that requests_retry_session creates a session with default values"""
    session = requests_retry_session()
    assert isinstance(session, requests.Session)
    
    # Check that adapters are mounted
    assert any(a.startswith("http://") for a in session.adapters.keys())
    assert any(a.startswith("https://") for a in session.adapters.keys())

def test_requests_retry_session_custom_params():
    """Test that requests_retry_session accepts custom parameters"""
    custom_session = Mock(spec=requests.Session)
    custom_session.mount = Mock()
    
    result = requests_retry_session(
        retries=5,
        backoff_factor=0.5,
        status_forcelist=(500, 501, 502),
        session=custom_session
    )
    
    assert result == custom_session
    assert custom_session.mount.call_count == 2

@patch('cloudproxy.check.requests_retry_session')
def test_fetch_ip_no_auth(mock_retry_session):
    """Test fetch_ip function with authentication disabled"""
    # Setup
    mock_response = Mock()
    mock_response.text = "192.168.1.1"
    mock_session = Mock()
    mock_session.get.return_value = mock_response
    mock_retry_session.return_value = mock_session
    
    # Set no_auth to True
    original_no_auth = settings.config["no_auth"]
    settings.config["no_auth"] = True
    
    try:
        # Execute
        result = fetch_ip("10.0.0.1")
        
        # Verify
        assert result == "192.168.1.1"
        expected_proxies = {
            "http": "http://10.0.0.1:8899",
            "https": "http://10.0.0.1:8899",
        }
        mock_session.get.assert_called_once_with(
            "https://api.ipify.org", proxies=expected_proxies, timeout=10
        )
    finally:
        # Restore original setting
        settings.config["no_auth"] = original_no_auth

@patch('cloudproxy.check.requests_retry_session')
def test_fetch_ip_with_auth(mock_retry_session):
    """Test fetch_ip function with authentication enabled"""
    # Setup
    mock_response = Mock()
    mock_response.text = "192.168.1.1"
    mock_session = Mock()
    mock_session.get.return_value = mock_response
    mock_retry_session.return_value = mock_session
    
    # Set no_auth to False and configure auth settings
    original_no_auth = settings.config["no_auth"]
    original_username = settings.config["auth"]["username"]
    original_password = settings.config["auth"]["password"]
    
    settings.config["no_auth"] = False
    settings.config["auth"]["username"] = "testuser"
    settings.config["auth"]["password"] = "testpass"
    
    try:
        # Execute
        result = fetch_ip("10.0.0.1")
        
        # Verify
        assert result == "192.168.1.1"
        expected_proxies = {
            "http": "http://testuser:testpass@10.0.0.1:8899",
            "https": "http://testuser:testpass@10.0.0.1:8899",
        }
        mock_session.get.assert_called_once_with(
            "https://api.ipify.org", proxies=expected_proxies, timeout=10
        )
    finally:
        # Restore original settings
        settings.config["no_auth"] = original_no_auth
        settings.config["auth"]["username"] = original_username
        settings.config["auth"]["password"] = original_password

@patch('cloudproxy.check.requests.get')
def test_check_alive_success(mock_get):
    """Test check_alive function with a successful response"""
    # Setup for successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    
    # Execute
    result = check_alive("10.0.0.1")
    
    # Verify
    assert result is True
    mock_get.assert_called_once_with(
        "http://ipecho.net/plain", 
        proxies={'http': "http://10.0.0.1:8899"}, 
        timeout=3
    )

@patch('cloudproxy.check.requests.get')
def test_check_alive_auth_required(mock_get):
    """Test check_alive function with 407 status code"""
    # Setup for auth required response
    mock_response = Mock()
    mock_response.status_code = 407  # Proxy Authentication Required
    mock_get.return_value = mock_response
    
    # Execute
    result = check_alive("10.0.0.1")
    
    # Verify
    assert result is True  # Should still return True for 407

@patch('cloudproxy.check.requests.get')
def test_check_alive_error_status(mock_get):
    """Test check_alive function with error status code"""
    # Setup for error response
    mock_response = Mock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response
    
    # Execute
    result = check_alive("10.0.0.1")
    
    # Verify
    assert result is False

@patch('cloudproxy.check.requests.get')
def test_check_alive_exception(mock_get):
    """Test check_alive function with exception"""
    # Setup to raise exception
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    
    # Execute
    result = check_alive("10.0.0.1")
    
    # Verify
    assert result is False 