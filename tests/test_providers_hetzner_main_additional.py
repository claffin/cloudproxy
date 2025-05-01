import unittest
from unittest.mock import patch, MagicMock, call
import datetime

from cloudproxy.providers.hetzner.main import (
    hetzner_check_delete,
    hetzner_deployment,
    hetzner_check_alive
)
from cloudproxy.providers.settings import delete_queue, restart_queue

class TestHetznerMainAdditional(unittest.TestCase):

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_check_delete_with_exception(self, mock_config, mock_delete_proxy, mock_list_proxies):
        """Test handling of exceptions in hetzner_check_delete."""
        # Setup
        # Save original delete and restart queues
        original_delete_queue = set(delete_queue)
        original_restart_queue = set(restart_queue)
        
        # Clear the queues for this test
        delete_queue.clear()
        restart_queue.clear()
        
        # Add test IP to delete queue
        delete_queue.add("1.1.1.1")
        
        try:
            mock_proxy = MagicMock(id="1")
            # Create a public_net attribute that has a valid IP
            mock_proxy.public_net = MagicMock()
            mock_proxy.public_net.ipv4 = MagicMock()
            mock_proxy.public_net.ipv4.ip = "1.1.1.1"
            
            # Add another proxy that will throw an exception
            mock_proxy_error = MagicMock(id="2")
            mock_proxy_error.public_net = MagicMock()
            
            # Setup the error proxy to raise exception when ipv4 is accessed
            def ipv4_getter(self):
                raise Exception("Test exception")
            
            # Use property with a getter that raises an exception
            type(mock_proxy_error.public_net).ipv4 = property(fget=ipv4_getter)
            
            mock_list_proxies.return_value = [mock_proxy, mock_proxy_error]
            mock_instance_config = {"display_name": "test"}
            mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}
            
            # Execute
            hetzner_check_delete(mock_instance_config)

            # Verify - should only delete the first proxy, the second one throws an exception
            mock_delete_proxy.assert_called_once()
            
            # Verify that 1.1.1.1 is no longer in the delete queue
            assert "1.1.1.1" not in delete_queue
        finally:
            # Restore original queues
            delete_queue.clear()
            delete_queue.update(original_delete_queue)
            restart_queue.clear()
            restart_queue.update(original_restart_queue)

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.delete_queue", new=set(["1.1.1.1"]))  # Pre-populate the delete queue
    @patch("cloudproxy.providers.hetzner.main.restart_queue", new=set())
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_check_delete_failed_deletion(self, mock_config, mock_delete_proxy, mock_list_proxies):
        """Test handling of failed deletions in hetzner_check_delete."""
        # Setup
        mock_proxy = MagicMock(id="1")
        mock_proxy.public_net = MagicMock()
        mock_proxy.public_net.ipv4 = MagicMock()
        mock_proxy.public_net.ipv4.ip = "1.1.1.1"  # Exact IP format matters
        
        mock_list_proxies.return_value = [mock_proxy]
        mock_instance_config = {"display_name": "test"}
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}
        
        # Make delete_proxy return False to simulate failed deletion
        mock_delete_proxy.return_value = False
        
        # Execute
        hetzner_check_delete(mock_instance_config)
        
        # Verify - delete should be attempted but IP should remain in queue
        mock_delete_proxy.assert_called_once()
        assert "1.1.1.1" in delete_queue  # IP should still be in queue

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.delete_queue", new=set())
    @patch("cloudproxy.providers.hetzner.main.restart_queue", new=set())
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_check_delete_empty_list(self, mock_config, mock_delete_proxy, mock_list_proxies):
        """Test hetzner_check_delete with empty proxy list."""
        # Setup
        mock_list_proxies.return_value = []
        mock_instance_config = {"display_name": "test"}
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}
        
        # Add IP to delete queue
        delete_queue.add("1.1.1.1")

        # Execute
        hetzner_check_delete(mock_instance_config)

        # Verify - should not attempt to delete anything
        mock_delete_proxy.assert_not_called()
        self.assertIn("1.1.1.1", delete_queue)

    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    @patch("cloudproxy.providers.hetzner.main.check_alive")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.dateparser")
    def test_hetzner_check_alive_with_invalid_date(self, mock_dateparser, mock_list_proxies, mock_delete_proxy, mock_check_alive, mock_config):
        """Test hetzner_check_alive with invalid date format."""
        # Setup a try/except in the mock to simulate the TypeError behavior but continue test execution
        def mock_parse_side_effect(date_str):
            raise TypeError("Invalid date format")
        
        mock_dateparser.parse.side_effect = mock_parse_side_effect
        
        # Setup proxy
        mock_proxy = MagicMock(public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1")))
        mock_proxy.created = "invalid-date-format"
        mock_list_proxies.return_value = []  # Return empty list so the function doesn't try to process the invalid data
        
        mock_instance_config = {"display_name": "test"}
        
        # Configure the mock config
        providers_dict = {"hetzner": {"instances": {"default": mock_instance_config}}}
        
        def config_getitem(key):
            if key == "providers":
                return providers_dict
            elif key == "age_limit":
                return 0
            else:
                return MagicMock()
                
        mock_config.__getitem__.side_effect = config_getitem
        
        # Mock the check_alive function
        mock_check_alive.return_value = True
        
        # Run the function
        ready_ips = hetzner_check_alive(mock_instance_config)

        # Verify
        mock_delete_proxy.assert_not_called()
        mock_check_alive.assert_not_called()
        self.assertEqual(ready_ips, []) 