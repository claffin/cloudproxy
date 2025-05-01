import pytest
from unittest.mock import patch, MagicMock
import digitalocean
from cloudproxy.providers.digitalocean.functions import (
    delete_proxy, 
    create_firewall, 
    DOFirewallExistsException
)


class TestDeleteProxyErrorHandling:
    """Tests for error handling in delete_proxy function."""
    
    @patch('cloudproxy.providers.digitalocean.functions.get_manager')
    def test_delete_proxy_with_droplet_object(self, mock_get_manager):
        """Test delete_proxy when called with a droplet object instead of just ID."""
        # Create a mock droplet object
        mock_droplet = MagicMock()
        mock_droplet.id = 12345
        
        # Mock the manager and its methods
        mock_manager = MagicMock()
        mock_manager.get_droplet.return_value = mock_droplet
        mock_get_manager.return_value = mock_manager
        
        # Mock the destroy method
        mock_droplet.destroy.return_value = True
        
        # Call the function with the droplet object
        result = delete_proxy(mock_droplet)
        
        # Verify the right methods were called
        mock_get_manager.assert_called_once()
        mock_manager.get_droplet.assert_called_once_with(12345)
        assert result == True
    
    @patch('cloudproxy.providers.digitalocean.functions.get_manager')
    def test_delete_proxy_droplet_not_found(self, mock_get_manager):
        """Test delete_proxy when the droplet is not found."""
        # Mock the manager
        mock_manager = MagicMock()
        # Make get_droplet raise an exception with "not found" in the message
        mock_manager.get_droplet.side_effect = Exception("Droplet not found")
        mock_get_manager.return_value = mock_manager
        
        # Call the function
        result = delete_proxy(12345)
        
        # Verify it considers a missing droplet as successfully deleted
        mock_manager.get_droplet.assert_called_once_with(12345)
        assert result == True
    
    @patch('cloudproxy.providers.digitalocean.functions.get_manager')
    def test_delete_proxy_with_droplet_object_not_found(self, mock_get_manager):
        """Test delete_proxy with a droplet object when the droplet is not found."""
        # Create a mock droplet object
        mock_droplet = MagicMock()
        mock_droplet.id = 12345
        
        # Mock the manager
        mock_manager = MagicMock()
        # Make get_droplet raise an exception with "not found" in the message
        mock_manager.get_droplet.side_effect = Exception("Droplet not found")
        mock_get_manager.return_value = mock_manager
        
        # Call the function with the droplet object
        result = delete_proxy(mock_droplet)
        
        # Verify it considers a missing droplet as successfully deleted
        mock_manager.get_droplet.assert_called_once_with(12345)
        assert result == True
    
    @patch('cloudproxy.providers.digitalocean.functions.get_manager')
    def test_delete_proxy_with_error_in_destroy(self, mock_get_manager):
        """Test delete_proxy when the destroy method raises an exception."""
        # Create mock droplet and manager
        mock_droplet = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_droplet.return_value = mock_droplet
        mock_get_manager.return_value = mock_manager
        
        # Make destroy raise a non-404 exception
        mock_droplet.destroy.side_effect = Exception("Some other error")
        
        # Call the function and expect the exception to be raised
        with pytest.raises(Exception, match="Some other error"):
            delete_proxy(12345)
        
        # Verify the right methods were called
        mock_manager.get_droplet.assert_called_once()
        mock_droplet.destroy.assert_called_once()
    
    @patch('cloudproxy.providers.digitalocean.functions.get_manager')
    def test_delete_proxy_with_404_in_destroy(self, mock_get_manager):
        """Test delete_proxy when the destroy method raises a 404 exception."""
        # Create mock droplet and manager
        mock_droplet = MagicMock()
        mock_manager = MagicMock()
        mock_manager.get_droplet.return_value = mock_droplet
        mock_get_manager.return_value = mock_manager
        
        # Make destroy raise a 404 exception
        mock_droplet.destroy.side_effect = Exception("404 Not Found")
        
        # Call the function
        result = delete_proxy(12345)
        
        # Verify it treats 404 as success
        mock_manager.get_droplet.assert_called_once()
        mock_droplet.destroy.assert_called_once()
        assert result == True 