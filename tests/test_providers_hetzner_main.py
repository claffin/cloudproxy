import unittest
from unittest.mock import patch, MagicMock
import datetime

from cloudproxy.providers.hetzner.main import (
    hetzner_deployment,
    hetzner_check_alive,
    hetzner_check_delete,
    hetzner_start,
)

class TestHetznerMain(unittest.TestCase):

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.create_proxy")
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_deployment_scale_down(self, mock_config, mock_create_proxy, mock_delete_proxy, mock_list_proxies):
        """Test scaling down Hetzner proxies."""
        mock_list_proxies.return_value = [MagicMock(public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1"))), MagicMock(public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.2")))]
        mock_instance_config = {"display_name": "test", "scaling": {"min_scaling": 1}}
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}

        hetzner_deployment(1, mock_instance_config)

        self.assertEqual(mock_delete_proxy.call_count, 1)
        mock_create_proxy.assert_not_called()

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.create_proxy")
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_deployment_scale_up(self, mock_config, mock_create_proxy, mock_delete_proxy, mock_list_proxies):
        """Test scaling up Hetzner proxies."""
        mock_list_proxies.return_value = []
        mock_instance_config = {"display_name": "test", "scaling": {"min_scaling": 2}}
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}

        hetzner_deployment(2, mock_instance_config)

        self.assertEqual(mock_create_proxy.call_count, 2)
        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.create_proxy")
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_deployment_min_met(self, mock_config, mock_create_proxy, mock_delete_proxy, mock_list_proxies):
        """Test when minimum scaling is already met."""
        mock_list_proxies.return_value = [MagicMock(public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1")))]
        mock_instance_config = {"display_name": "test", "scaling": {"min_scaling": 1}}
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}

        hetzner_deployment(1, mock_instance_config)

        mock_delete_proxy.assert_not_called()
        mock_create_proxy.assert_not_called()

    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    @patch("cloudproxy.providers.hetzner.main.check_alive")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    def test_hetzner_check_alive_recycling(self, mock_list_proxies, mock_delete_proxy, mock_check_alive, mock_config):
        """Test recycling of Hetzner proxies based on age limit."""
        # Setup proxy
        mock_proxy = MagicMock(public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1")))
        mock_proxy.created = "2023-01-01T00:00:00Z"
        mock_list_proxies.return_value = [mock_proxy]
        mock_instance_config = {"display_name": "test"}
        
        # Configure the mock config
        providers_dict = {"hetzner": {"instances": {"default": mock_instance_config}}}
        
        def config_getitem(key):
            if key == "providers":
                return providers_dict
            elif key == "age_limit":
                return 100  # Return an actual integer
            else:
                return MagicMock()
                
        mock_config.__getitem__.side_effect = config_getitem
        
        # Create a module-level function to replace the datetime operations
        # This function will be called when the implementation calculates elapsed time
        def mock_elapsed_time(*args, **kwargs):
            # Return a timedelta that's greater than age_limit (100 seconds)
            return datetime.timedelta(seconds=101)
            
        # Patch the module-level function
        with patch("cloudproxy.providers.hetzner.main.datetime") as mock_datetime:
            # Setup the datetime mock to return our custom elapsed time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.timezone = datetime.timezone
            
            # Create a mock datetime class with a now method
            class MockDatetime:
                @staticmethod
                def now(tz=None):
                    return datetime.datetime(2023, 1, 1, 0, 2, 0, tzinfo=datetime.timezone.utc)
                    
            # Replace the datetime.datetime class with our mock
            mock_datetime.datetime = MockDatetime
            
            # Mock dateparser.parse to return a fixed datetime
            with patch("cloudproxy.providers.hetzner.main.dateparser.parse") as mock_parse:
                mock_parse.return_value = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
                
                # Run the function
                hetzner_check_alive(mock_instance_config)

        # Use the instance config directly in assertion
        mock_delete_proxy.assert_called_once_with(mock_proxy, instance_id="default")
        mock_check_alive.assert_not_called()

    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    @patch("cloudproxy.providers.hetzner.main.check_alive")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    def test_hetzner_check_alive_alive(self, mock_list_proxies, mock_delete_proxy, mock_check_alive, mock_config):
        """Test checking alive Hetzner proxies."""
        # Setup proxy
        mock_proxy = MagicMock(public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1")))
        mock_proxy.created = "2023-01-01T00:00:00Z"
        mock_list_proxies.return_value = [mock_proxy]
        mock_instance_config = {"display_name": "test"}
        
        # Configure the mock config
        providers_dict = {"hetzner": {"instances": {"default": mock_instance_config}}}
        
        def config_getitem(key):
            if key == "providers":
                return providers_dict
            elif key == "age_limit":
                return 0  # Return an actual integer
            else:
                return MagicMock()
                
        mock_config.__getitem__.side_effect = config_getitem
        
        # Mock the check_alive function to simulate a proxy that's alive
        mock_check_alive.return_value = True
        
        # Patch the module-level function
        with patch("cloudproxy.providers.hetzner.main.datetime") as mock_datetime:
            # Setup the datetime mock to return our custom elapsed time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.timezone = datetime.timezone
            
            # Create a mock datetime class with a now method
            class MockDatetime:
                @staticmethod
                def now(tz=None):
                    return datetime.datetime(2023, 1, 1, 0, 0, 1, tzinfo=datetime.timezone.utc)
                    
            # Replace the datetime.datetime class with our mock
            mock_datetime.datetime = MockDatetime
            
            # Mock dateparser.parse to return a fixed datetime
            with patch("cloudproxy.providers.hetzner.main.dateparser.parse") as mock_parse:
                mock_parse.return_value = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
                
                # Run the function
                ready_ips = hetzner_check_alive(mock_instance_config)

        mock_delete_proxy.assert_not_called()
        mock_check_alive.assert_called_once_with("1.1.1.1")
        self.assertEqual(ready_ips, ["1.1.1.1"])

    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    @patch("cloudproxy.providers.hetzner.main.check_alive")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    def test_hetzner_check_alive_too_long(self, mock_list_proxies, mock_delete_proxy, mock_check_alive, mock_config):
        """Test deleting Hetzner proxies that take too long to become alive."""
        # Setup proxy
        mock_proxy = MagicMock(public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1")))
        mock_proxy.created = "2023-01-01T00:00:00Z"
        mock_list_proxies.return_value = [mock_proxy]
        mock_instance_config = {"display_name": "test"}
        
        # Configure the mock config
        providers_dict = {"hetzner": {"instances": {"default": mock_instance_config}}}
        
        def config_getitem(key):
            if key == "providers":
                return providers_dict
            elif key == "age_limit":
                return 0  # Return an actual integer
            else:
                return MagicMock()
                
        mock_config.__getitem__.side_effect = config_getitem
        
        # Mock the check_alive function to simulate a proxy that's not alive
        mock_check_alive.return_value = False
        
        # Patch the module-level function
        with patch("cloudproxy.providers.hetzner.main.datetime") as mock_datetime:
            # Setup the datetime mock to return our custom elapsed time
            mock_datetime.timedelta = datetime.timedelta
            mock_datetime.timezone = datetime.timezone
            
            # Create a mock datetime class with a now method
            class MockDatetime:
                @staticmethod
                def now(tz=None):
                    return datetime.datetime(2023, 1, 1, 0, 11, 0, tzinfo=datetime.timezone.utc)
                    
            # Replace the datetime.datetime class with our mock
            mock_datetime.datetime = MockDatetime
            
            # Mock dateparser.parse to return a fixed datetime
            with patch("cloudproxy.providers.hetzner.main.dateparser.parse") as mock_parse:
                mock_parse.return_value = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
                
                # Run the function
                ready_ips = hetzner_check_alive(mock_instance_config)

        # Use the instance config directly in assertion
        mock_delete_proxy.assert_called_once_with(mock_proxy, instance_id="default")
        mock_check_alive.assert_called_once_with("1.1.1.1")
        self.assertEqual(ready_ips, [])

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.hetzner.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_check_delete_in_queue(self, mock_config, mock_restart_queue, mock_delete_queue, mock_delete_proxy, mock_list_proxies):
        """Test deleting Hetzner proxies that are in the delete or restart queue."""
        mock_proxy_delete = MagicMock(id="1", public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1")))
        mock_proxy_restart = MagicMock(id="2", public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.2")))
        mock_list_proxies.return_value = [mock_proxy_delete, mock_proxy_restart]
        mock_delete_queue.extend(["1.1.1.1"])
        mock_restart_queue.extend(["1.1.1.2"])
        mock_instance_config = {"display_name": "test"}
        # Set attributes directly on the mock config
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}
        mock_delete_proxy.return_value = True

        hetzner_check_delete(mock_instance_config)

        self.assertEqual(mock_delete_proxy.call_count, 2)
        # Use the instance config directly in assertions
        mock_delete_proxy.assert_any_call(mock_proxy_delete, instance_id="default")
        mock_delete_proxy.assert_any_call(mock_proxy_restart, instance_id="default")
        self.assertNotIn("1.1.1.1", mock_delete_queue)
        self.assertNotIn("1.1.1.2", mock_restart_queue)

    @patch("cloudproxy.providers.hetzner.main.list_proxies")
    @patch("cloudproxy.providers.hetzner.main.delete_proxy")
    @patch("cloudproxy.providers.hetzner.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.hetzner.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_check_delete_not_in_queue(self, mock_config, mock_restart_queue, mock_delete_queue, mock_delete_proxy, mock_list_proxies):
        """Test that Hetzner proxies not in queues are not deleted."""
        mock_proxy = MagicMock(id="1", public_net=MagicMock(ipv4=MagicMock(ip="1.1.1.1")))
        mock_list_proxies.return_value = [mock_proxy]
        mock_delete_queue.clear()
        mock_restart_queue.clear()
        mock_instance_config = {"display_name": "test"}
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}

        hetzner_check_delete(mock_instance_config)

        mock_delete_proxy.assert_not_called()
        self.assertNotIn("1.1.1.1", mock_delete_queue)
        self.assertNotIn("1.1.1.1", mock_restart_queue)

    @patch("cloudproxy.providers.hetzner.main.hetzner_check_delete")
    @patch("cloudproxy.providers.hetzner.main.hetzner_deployment")
    @patch("cloudproxy.providers.hetzner.main.hetzner_check_alive")
    @patch("cloudproxy.providers.hetzner.main.config", new_callable=MagicMock)
    def test_hetzner_start(self, mock_config, mock_hetzner_check_alive, mock_hetzner_deployment, mock_hetzner_check_delete):
        """Test the main Hetzner start function."""
        mock_instance_config = {"scaling": {"min_scaling": 1}, "display_name": "test"} # Added display_name for consistency
        # Set attributes directly on the mock config
        mock_config["providers"] = {"hetzner": {"instances": {"default": mock_instance_config}}}
        mock_hetzner_check_alive.return_value = ["1.1.1.1"]

        ready_ips = hetzner_start(mock_instance_config, instance_id="default")

        # Use the instance config directly in assertions
        mock_hetzner_check_delete.assert_called_once_with(mock_instance_config, instance_id="default")
        mock_hetzner_deployment.assert_called_once_with(1, mock_instance_config, instance_id="default")
        mock_hetzner_check_alive.assert_called_once_with(mock_instance_config, instance_id="default")
        self.assertEqual(ready_ips, ["1.1.1.1"])
