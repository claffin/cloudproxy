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
    original_providers = settings.config["providers"].copy()
    
    yield
    
    # Restore original values
    settings.config["providers"] = original_providers

@pytest.fixture
def test_instance_config():
    """Test instance configuration for multiple providers"""
    return {
        "aws": {
            "enabled": True,
            "ips": [],
            "scaling": {"min_scaling": 2, "max_scaling": 5},
            "size": "t3.micro",
            "region": "us-west-2",
            "display_name": "Test AWS",
            "secrets": {
                "access_key_id": "test-key",
                "secret_access_key": "test-secret"
            }
        },
        "digitalocean": {
            "enabled": True,
            "ips": [],
            "scaling": {"min_scaling": 1, "max_scaling": 3},
            "size": "s-2vcpu-2gb",
            "region": "sfo2",
            "display_name": "Test DO",
            "secrets": {
                "access_token": "test-token"
            }
        },
        "gcp": {
            "enabled": True,
            "ips": [],
            "scaling": {"min_scaling": 1, "max_scaling": 2},
            "size": "e2-medium",
            "zone": "us-west1-a",
            "display_name": "Test GCP",
            "secrets": {
                "service_account_key": "test-key"
            }
        },
        "hetzner": {
            "enabled": True,
            "ips": [],
            "scaling": {"min_scaling": 2, "max_scaling": 4},
            "size": "cx21",
            "location": "fsn1",
            "display_name": "Test Hetzner",
            "secrets": {
                "access_token": "test-token"
            }
        }
    }


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
    assert settings.config["providers"]["digitalocean"]["instances"]["default"]["ips"] == expected_ips
    mock_do_start.assert_called_once()
    
    # Check that do_start was called with the default instance config
    default_config = settings.config["providers"]["digitalocean"]["instances"]["default"]
    mock_do_start.assert_called_once_with(default_config, instance_id="default")

@patch('cloudproxy.providers.manager.do_start')
def test_do_manager_custom_instance(mock_do_start, setup_manager_test, test_instance_config):
    """Test DigitalOcean manager function with custom instance name"""
    # Setup - mock what do_start returns
    expected_ips = ["192.168.1.1", "192.168.1.2"]
    mock_do_start.return_value = expected_ips.copy()
    
    # Setup test instance in the config
    settings.config["providers"]["digitalocean"]["instances"]["test"] = test_instance_config["digitalocean"]
    
    # Execute with custom instance name
    result = do_manager("test")
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["digitalocean"]["instances"]["test"]["ips"] == expected_ips
    
    # Check that do_start was called with the test instance config
    test_config = settings.config["providers"]["digitalocean"]["instances"]["test"]
    mock_do_start.assert_called_once_with(test_config, instance_id="test")


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
    assert settings.config["providers"]["aws"]["instances"]["default"]["ips"] == expected_ips
    
    # Check that aws_start was called with the default instance config
    default_config = settings.config["providers"]["aws"]["instances"]["default"]
    mock_aws_start.assert_called_once_with(default_config, instance_id="default")

@patch('cloudproxy.providers.manager.aws_start')
def test_aws_manager_custom_instance(mock_aws_start, setup_manager_test, test_instance_config):
    """Test AWS manager function with custom instance name"""
    # Setup - mock what aws_start returns
    expected_ips = ["10.0.0.1", "10.0.0.2"]
    mock_aws_start.return_value = expected_ips.copy()
    
    # Setup test instance in the config
    settings.config["providers"]["aws"]["instances"]["production"] = test_instance_config["aws"]
    
    # Execute with custom instance name
    result = aws_manager("production")
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["aws"]["instances"]["production"]["ips"] == expected_ips
    
    # Check that aws_start was called with the test instance config
    test_config = settings.config["providers"]["aws"]["instances"]["production"]
    mock_aws_start.assert_called_once_with(test_config, instance_id="production")


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
    assert settings.config["providers"]["gcp"]["instances"]["default"]["ips"] == expected_ips
    
    # Check that gcp_start was called with the default instance config
    default_config = settings.config["providers"]["gcp"]["instances"]["default"]
    mock_gcp_start.assert_called_once_with(default_config, instance_id="default")

@patch('cloudproxy.providers.manager.gcp_start')
def test_gcp_manager_custom_instance(mock_gcp_start, setup_manager_test, test_instance_config):
    """Test GCP manager function with custom instance name"""
    # Setup - mock what gcp_start returns
    expected_ips = ["172.16.0.1", "172.16.0.2"]
    mock_gcp_start.return_value = expected_ips.copy()
    
    # Setup test instance in the config
    settings.config["providers"]["gcp"]["instances"]["dev"] = test_instance_config["gcp"]
    
    # Execute with custom instance name
    result = gcp_manager("dev")
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["gcp"]["instances"]["dev"]["ips"] == expected_ips
    
    # Check that gcp_start was called with the test instance config
    test_config = settings.config["providers"]["gcp"]["instances"]["dev"]
    mock_gcp_start.assert_called_once_with(test_config, instance_id="dev")


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
    assert settings.config["providers"]["hetzner"]["instances"]["default"]["ips"] == expected_ips
    
    # Check that hetzner_start was called with the default instance config
    default_config = settings.config["providers"]["hetzner"]["instances"]["default"]
    mock_hetzner_start.assert_called_once_with(default_config, instance_id="default")

@patch('cloudproxy.providers.manager.hetzner_start')
def test_hetzner_manager_custom_instance(mock_hetzner_start, setup_manager_test, test_instance_config):
    """Test Hetzner manager function with custom instance name"""
    # Setup - mock what hetzner_start returns
    expected_ips = ["1.2.3.4", "5.6.7.8"]
    mock_hetzner_start.return_value = expected_ips.copy()
    
    # Setup test instance in the config
    settings.config["providers"]["hetzner"]["instances"]["highcpu"] = test_instance_config["hetzner"]
    
    # Execute with custom instance name
    result = hetzner_manager("highcpu")
    
    # Verify
    assert result == expected_ips
    assert settings.config["providers"]["hetzner"]["instances"]["highcpu"]["ips"] == expected_ips
    
    # Check that hetzner_start was called with the test instance config
    test_config = settings.config["providers"]["hetzner"]["instances"]["highcpu"]
    mock_hetzner_start.assert_called_once_with(test_config, instance_id="highcpu")


# Test error handling in managers
@patch('cloudproxy.providers.manager.do_start')
def test_do_manager_empty_response(mock_do_start, setup_manager_test):
    """Test DigitalOcean manager with empty response"""
    # Setup - mock an empty response
    mock_do_start.return_value = []
    
    # Set initial IPs
    settings.config["providers"]["digitalocean"]["instances"]["default"]["ips"] = ["old.ip.address"]
    
    # Execute
    result = do_manager()
    
    # Verify
    assert result == []
    assert settings.config["providers"]["digitalocean"]["instances"]["default"]["ips"] == []


@patch('cloudproxy.providers.manager.aws_start')
def test_aws_manager_exception(mock_aws_start, setup_manager_test):
    """Test AWS manager with an exception in aws_start"""
    # Setup - mock aws_start to raise an exception
    mock_aws_start.side_effect = Exception("Test exception")
    
    # Set initial IPs
    original_ips = ["old.ip.address"]
    settings.config["providers"]["aws"]["instances"]["default"]["ips"] = original_ips.copy()
    
    # Execute - this should catch the exception and return an empty list
    with pytest.raises(Exception):
        aws_manager()
        
@patch('cloudproxy.providers.manager.aws_start')
def test_aws_manager_custom_instance_exception(mock_aws_start, setup_manager_test, test_instance_config):
    """Test AWS manager with custom instance and an exception"""
    # Setup - mock aws_start to raise an exception
    mock_aws_start.side_effect = Exception("Test exception")
    
    # Setup test instance in the config
    settings.config["providers"]["aws"]["instances"]["prod"] = test_instance_config["aws"]
    settings.config["providers"]["aws"]["instances"]["prod"]["ips"] = ["old.prod.ip"]
    
    # Execute - this should catch the exception and return an empty list
    with pytest.raises(Exception):
        aws_manager("prod") 