import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open

from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth


# Create a mock user data script that represents the content of user_data.sh
MOCK_USER_DATA = """#!/bin/bash
# Install Tinyproxy
sudo apt-get update
sudo apt-get install -y tinyproxy ufw

# Configure Tinyproxy
sudo mv /etc/tinyproxy/tinyproxy.conf /etc/tinyproxy/tinyproxy.conf.bak
sudo bash -c "cat > /etc/tinyproxy/tinyproxy.conf" << 'EOL'
User nobody
Group nogroup
Port 8899
Timeout 600
DefaultErrorFile "/usr/share/tinyproxy/default.html"
StatHost "127.0.0.1"
StatFile "/usr/share/tinyproxy/stats.html"
LogFile "/var/log/tinyproxy/tinyproxy.log"
LogLevel Info
PidFile "/run/tinyproxy/tinyproxy.pid"
MaxClients 100
Allow 127.0.0.1

BasicAuth PROXY_USERNAME PROXY_PASSWORD

ConnectPort 443
ConnectPort 563
EOL

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 8899/tcp
sudo ufw enable
"""


@pytest.fixture
def setup_config_test():
    """Save original settings and restore them after test"""
    # Save original settings
    original_no_auth = settings.config.get("no_auth", False)
    original_only_host_ip = settings.config.get("only_host_ip", False)
    
    # Run the test
    yield
    
    # Restore original settings
    settings.config["no_auth"] = original_no_auth
    settings.config["only_host_ip"] = original_only_host_ip


def test_set_auth_with_auth(setup_config_test):
    """Test set_auth with authentication enabled"""
    # Set config values
    settings.config["no_auth"] = False
    settings.config["only_host_ip"] = False
    
    # Mock the open function to return our mock user_data content
    with patch("builtins.open", mock_open(read_data=MOCK_USER_DATA)):
        result = set_auth("testuser", "testpass")
    
    # Verify username and password were replaced
    assert "BasicAuth testuser testpass" in result
    assert "PROXY_USERNAME" not in result
    assert "PROXY_PASSWORD" not in result


def test_set_auth_without_auth(setup_config_test):
    """Test set_auth with authentication disabled"""
    # Set config values
    settings.config["no_auth"] = True
    settings.config["only_host_ip"] = False
    
    # Mock the open function to return our mock user_data content
    with patch("builtins.open", mock_open(read_data=MOCK_USER_DATA)):
        result = set_auth("testuser", "testpass")
    
    # Verify BasicAuth line was removed
    assert "\nBasicAuth PROXY_USERNAME PROXY_PASSWORD\n" not in result
    # When only_host_ip is False, Allow should be changed to 0.0.0.0/0
    assert "Allow 0.0.0.0/0" in result


def test_set_auth_with_host_ip(setup_config_test):
    """Test set_auth with host IP enabled"""
    # Set config values
    settings.config["no_auth"] = False
    settings.config["only_host_ip"] = True
    
    # Mock the requests.get call to return a specific IP
    mock_response = MagicMock()
    mock_response.text = "192.168.1.1"
    
    with patch("cloudproxy.providers.config.requests.get", return_value=mock_response):
        # Mock the open function to return our mock user_data content
        with patch("builtins.open", mock_open(read_data=MOCK_USER_DATA)):
            result = set_auth("testuser", "testpass")
    
    # Verify IP address was included in UFW rules and Allow rule
    assert "sudo ufw allow from 192.168.1.1 to any port 22 proto tcp" in result
    assert "sudo ufw allow from 192.168.1.1 to any port 8899 proto tcp" in result
    assert "Allow 127.0.0.1\nAllow 192.168.1.1" in result
    assert "BasicAuth testuser testpass" in result


def test_set_auth_with_both_options(setup_config_test):
    """Test set_auth with both no_auth and only_host_ip enabled"""
    # Set config values
    settings.config["no_auth"] = True
    settings.config["only_host_ip"] = True
    
    # Mock the requests.get call to return a specific IP
    mock_response = MagicMock()
    mock_response.text = "192.168.1.1"
    
    with patch("cloudproxy.providers.config.requests.get", return_value=mock_response):
        # Mock the open function to return our mock user_data content
        with patch("builtins.open", mock_open(read_data=MOCK_USER_DATA)):
            result = set_auth("testuser", "testpass")
    
    # Verify both modifications were applied
    assert "\nBasicAuth PROXY_USERNAME PROXY_PASSWORD\n" not in result
    assert "sudo ufw allow from 192.168.1.1 to any port 22 proto tcp" in result
    assert "Allow 127.0.0.1\nAllow 192.168.1.1" in result 