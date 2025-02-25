import pytest
from unittest.mock import Mock, patch, MagicMock
import digitalocean
from cloudproxy.providers.digitalocean.functions import (
    create_firewall, DOFirewallExistsException
)

class TestDigitalOceanFirewall:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup before each test and cleanup after"""
        yield  # This is where the testing happens

    def test_create_firewall(self, mocker):
        """Test successful firewall creation"""
        # Mock the DigitalOcean client and firewall
        mock_manager = Mock()
        mock_firewall = Mock()
        mock_firewall.id = "123456"
        
        # Mock the digitalocean.Manager and FirewallManager
        mocker.patch(
            'cloudproxy.providers.digitalocean.functions.digitalocean.Manager',
            return_value=mock_manager
        )
        
        # Mock the Firewall class
        mock_fw = Mock()
        mocker.patch(
            'cloudproxy.providers.digitalocean.functions.digitalocean.Firewall',
            return_value=mock_fw
        )
        
        mock_manager.get_all_firewalls = MagicMock(return_value=[])
        
        # Call the function
        create_firewall()
        
        # Verify the expected behaviors
        mock_fw.create.assert_called_once()
        
    def test_create_firewall_already_exists(self, mocker):
        """Test handling of duplicate firewall name"""
        # Mock the DataReadError class
        class MockDataReadError(Exception):
            pass
            
        mocker.patch(
            'cloudproxy.providers.digitalocean.functions.digitalocean.DataReadError',
            MockDataReadError
        )
        
        # Mock the Firewall class
        mock_fw = Mock()
        mocker.patch(
            'cloudproxy.providers.digitalocean.functions.digitalocean.Firewall',
            return_value=mock_fw
        )
        
        # Set up the error
        mock_fw.create.side_effect = MockDataReadError('duplicate name')
        
        # Call the function and expect exception
        with pytest.raises(DOFirewallExistsException) as exc_info:
            create_firewall()
        
        # Verify the exception message
        assert "Firewall already exists" in str(exc_info.value)
        
    def test_create_firewall_other_error(self, mocker):
        """Test handling of other errors during firewall creation"""
        # Mock the Firewall class
        mock_fw = Mock()
        mocker.patch(
            'cloudproxy.providers.digitalocean.functions.digitalocean.Firewall',
            return_value=mock_fw
        )
        
        # Set up a general exception
        mock_fw.create.side_effect = Exception("API Error")
        
        # Call the function - it should propagate the exception
        with pytest.raises(Exception) as exc_info:
            create_firewall()
        
        # Verify the exception message
        assert "API Error" in str(exc_info.value)
        mock_fw.create.assert_called_once() 