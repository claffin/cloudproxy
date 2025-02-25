import pytest
from unittest.mock import patch, Mock

from cloudproxy.providers import settings
from cloudproxy.providers.manager import (
    do_manager,
    aws_manager,
    gcp_manager,
    hetzner_manager
)


# Fixture to save and restore settings
@pytest.fixture
def setup_manager_test():
    """Fixture to save and restore provider IP lists"""
    # Save original values
    original_do_ips = settings.config["providers"]["digitalocean"]["ips"].copy()
    original_aws_ips = settings.config["providers"]["aws"]["ips"].copy()
    original_gcp_ips = settings.config["providers"]["gcp"]["ips"].copy()
    original_hetzner_ips = settings.config["providers"]["hetzner"]["ips"].copy()
    
    yield
    
    # Restore original values
    settings.config["providers"]["digitalocean"]["ips"] = original_do_ips
    settings.config["providers"]["aws"]["ips"] = original_aws_ips
    settings.config["providers"]["gcp"]["ips"] = original_gcp_ips
    settings.config["providers"]["hetzner"]["ips"] = original_hetzner_ips


# Test DigitalOcean manager
@patch('cloudproxy.providers.manager.do_start')
def test_do_manager(mock_do_start, setup_manager_test):
    """Test DigitalOcean manager function"""
    # Setup - mock what do_start returns
    expected_ips = ["192.168.1.1", "192.168.1.2"]
    mock_do_start.return_value = expected_ips.copy()
    
    # Execute
    result = do_manager()
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["digitalocean"]["ips"] == expected_ips
    mock_do_start.assert_called_once()


# Test AWS manager
@patch('cloudproxy.providers.manager.aws_start')
def test_aws_manager(mock_aws_start, setup_manager_test):
    """Test AWS manager function"""
    # Setup - mock what aws_start returns
    expected_ips = ["10.0.0.1", "10.0.0.2"]
    mock_aws_start.return_value = expected_ips.copy()
    
    # Execute
    result = aws_manager()
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["aws"]["ips"] == expected_ips
    mock_aws_start.assert_called_once()


# Test GCP manager
@patch('cloudproxy.providers.manager.gcp_start')
def test_gcp_manager(mock_gcp_start, setup_manager_test):
    """Test GCP manager function"""
    # Setup - mock what gcp_start returns
    expected_ips = ["172.16.0.1", "172.16.0.2"]
    mock_gcp_start.return_value = expected_ips.copy()
    
    # Execute
    result = gcp_manager()
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["gcp"]["ips"] == expected_ips
    mock_gcp_start.assert_called_once()


# Test Hetzner manager
@patch('cloudproxy.providers.manager.hetzner_start')
def test_hetzner_manager(mock_hetzner_start, setup_manager_test):
    """Test Hetzner manager function"""
    # Setup - mock what hetzner_start returns
    expected_ips = ["1.2.3.4", "5.6.7.8"]
    mock_hetzner_start.return_value = expected_ips.copy()
    
    # Execute
    result = hetzner_manager()
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["hetzner"]["ips"] == expected_ips
    mock_hetzner_start.assert_called_once()


# Test error handling in managers
@patch('cloudproxy.providers.manager.do_start')
def test_do_manager_empty_response(mock_do_start, setup_manager_test):
    """Test DigitalOcean manager with empty response"""
    # Setup - mock an empty response
    mock_do_start.return_value = []
    
    # Set initial IPs
    settings.config["providers"]["digitalocean"]["ips"] = ["old.ip.address"]
    
    # Execute
    result = do_manager()
    
    # Verify
    assert result == []
    assert settings.config["providers"]["digitalocean"]["ips"] == []


@patch('cloudproxy.providers.manager.aws_start')
def test_aws_manager_exception(mock_aws_start, setup_manager_test):
    """Test AWS manager with an exception in aws_start"""
    # Setup - mock aws_start to raise an exception
    mock_aws_start.side_effect = Exception("Test exception")
    
    # Set initial IPs
    original_ips = ["old.ip.address"]
    settings.config["providers"]["aws"]["ips"] = original_ips.copy()
    
    # Execute - this should catch the exception and return an empty list
    with pytest.raises(Exception):
        aws_manager() 