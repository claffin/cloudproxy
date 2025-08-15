import unittest
from unittest.mock import patch, MagicMock, call
import datetime
import dateparser
import pytest
from datetime import timezone

from cloudproxy.providers.digitalocean.main import (
    do_deployment,
    do_check_alive,
    do_check_delete,
    do_fw,
    do_start,
)
from cloudproxy.providers.digitalocean.functions import DOFirewallExistsException
from cloudproxy.providers.settings import delete_queue, restart_queue, config


class TestDigitalOceanMainCoverage(unittest.TestCase):

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.create_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_deployment_deploy_new(
        self, mock_config, mock_delete_proxy, mock_create_proxy, mock_list_droplets
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 3}
        }
        mock_list_droplets.return_value = [MagicMock(), MagicMock()]  # 2 existing droplets

        do_deployment(3)

        self.assertEqual(mock_create_proxy.call_count, 1)  # Should create 1 new droplet
        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.create_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_deployment_destroy_overprovisioned(
        self, mock_config, mock_delete_proxy, mock_create_proxy, mock_list_droplets
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 1}
        }
        mock_list_droplets.return_value = [
            MagicMock(ip_address="1.1.1.1"),
            MagicMock(ip_address="2.2.2.2"),
        ]  # 2 existing droplets

        do_deployment(1)

        self.assertEqual(mock_delete_proxy.call_count, 1)  # Should delete 1 droplet
        mock_create_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.create_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_deployment_min_scaling_met(
        self, mock_config, mock_delete_proxy, mock_create_proxy, mock_list_droplets
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 2}
        }
        mock_list_droplets.return_value = [
            MagicMock(),
            MagicMock(),
        ]  # 2 existing droplets

        do_deployment(2)

        mock_create_proxy.assert_not_called()
        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.check_alive")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.dateparser.parse")
    @patch("cloudproxy.providers.digitalocean.main.datetime")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_alive_pending_droplet(
        self,
        mock_config,
        mock_datetime,
        mock_dateparser_parse,
        mock_delete_proxy,
        mock_check_alive,
        mock_list_droplets,
    ):
        mock_config["age_limit"] = 0
        mock_datetime.datetime.now.return_value = datetime.datetime(
            2023, 1, 1, 12, 5, 0, tzinfo=datetime.timezone.utc
        )
        mock_dateparser_parse.return_value = datetime.datetime(
            2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc
        )  # 5 minutes old
        mock_list_droplets.return_value = [MagicMock(ip_address="1.1.1.1")]
        mock_check_alive.return_value = False
        mock_dateparser_parse.side_effect = TypeError # Simulate pending state

        ip_ready = do_check_alive()

        self.assertEqual(ip_ready, [])
        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_in_delete_queue(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_delete_queue.append("1.1.1.1")
        mock_list_droplets.return_value = [MagicMock(id=123, ip_address="1.1.1.1")]
        mock_delete_proxy.return_value = True

        do_check_delete()

        mock_delete_proxy.assert_called_once()
        self.assertNotIn("1.1.1.1", mock_delete_queue)

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_in_restart_queue(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_restart_queue.append("1.1.1.1")
        mock_list_droplets.return_value = [MagicMock(id=123, ip_address="1.1.1.1")]
        mock_delete_proxy.return_value = True

        do_check_delete()

        mock_delete_proxy.assert_called_once()
        self.assertNotIn("1.1.1.1", mock_restart_queue)

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_not_in_queues(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_list_droplets.return_value = [MagicMock(id=123, ip_address="1.1.1.1")]

        do_check_delete()

        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.list_droplets")
    @patch("cloudproxy.providers.digitalocean.main.delete_proxy")
    @patch("cloudproxy.providers.digitalocean.main.delete_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.restart_queue", new_callable=list)
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_check_delete_no_droplets(
        self,
        mock_config,
        mock_restart_queue,
        mock_delete_queue,
        mock_delete_proxy,
        mock_list_droplets,
    ):
        mock_list_droplets.return_value = []

        do_check_delete()

        mock_delete_proxy.assert_not_called()

    @patch("cloudproxy.providers.digitalocean.main.create_firewall")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_fw_create_success(self, mock_config, mock_create_firewall):
        mock_config["providers"]["digitalocean"]["instances"] = {
            "default": {"some_config": "value"}
        }

        do_fw()

        mock_create_firewall.assert_called_once()

    @patch("cloudproxy.providers.digitalocean.main.create_firewall")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_fw_firewall_exists(self, mock_config, mock_create_firewall):
        mock_config["providers"]["digitalocean"]["instances"] = {
            "default": {"some_config": "value"}
        }
        mock_create_firewall.side_effect = DOFirewallExistsException

        do_fw()

        mock_create_firewall.assert_called_once()

    @patch("cloudproxy.providers.digitalocean.main.create_firewall")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    @patch("cloudproxy.providers.digitalocean.main.logger")
    def test_do_fw_other_exception(self, mock_logger, mock_config, mock_create_firewall):
        mock_config["providers"]["digitalocean"]["instances"] = {
            "default": {"some_config": "value"}
        }
        mock_create_firewall.side_effect = Exception("Some error")

        do_fw()

        mock_create_firewall.assert_called_once()
        mock_logger.error.assert_called_once()

    @patch("cloudproxy.providers.digitalocean.main.do_fw")
    @patch("cloudproxy.providers.digitalocean.main.do_check_delete")
    @patch("cloudproxy.providers.digitalocean.main.do_check_alive")
    @patch("cloudproxy.providers.digitalocean.main.do_deployment")
    @patch("cloudproxy.providers.digitalocean.main.config", new_callable=MagicMock)
    def test_do_start(
        self,
        mock_config,
        mock_do_deployment,
        mock_do_check_alive,
        mock_do_check_delete,
        mock_do_fw,
    ):
        mock_config["providers"]["digitalocean"]["instances"]["default"] = {
            "scaling": {"min_scaling": 1}
        }
        mock_do_check_alive.side_effect = [[], ["1.1.1.1"]] # Simulate initial check and final check

        do_start()

        mock_do_fw.assert_called_once()
        mock_do_check_delete.assert_called_once()
        self.assertEqual(mock_do_check_alive.call_count, 2)
        mock_do_deployment.assert_called_once()


class MockDroplet:
    def __init__(self, id, ip_address, created_at=None):
        self.id = id
        self.ip_address = ip_address
        self.created_at = created_at or datetime.datetime.now(timezone.utc).isoformat()
        self.status = "active"
        self.tags = ["cloudproxy"]

@pytest.fixture
def setup_queues():
    """Setup and restore delete and restart queues"""
    original_delete_queue = delete_queue.copy()
    original_restart_queue = restart_queue.copy()
    
    # Clear queues for testing
    delete_queue.clear()
    restart_queue.clear()
    
    yield
    
    # Restore original queues
    delete_queue.clear()
    delete_queue.update(original_delete_queue)
    restart_queue.clear()
    restart_queue.update(original_restart_queue)

@pytest.fixture
def mock_droplets():
    """Setup mock droplets for testing"""
    now = datetime.datetime.now(timezone.utc)
    ten_minutes_ago = (now - datetime.timedelta(minutes=10)).isoformat()
    two_hours_ago = (now - datetime.timedelta(hours=2)).isoformat()
    
    return [
        MockDroplet(1, "1.2.3.4", now.isoformat()),  # Just created
        MockDroplet(2, "5.6.7.8", ten_minutes_ago),  # 10 minutes old
        MockDroplet(3, "9.10.11.12", two_hours_ago)  # 2 hours old (potentially beyond age limit)
    ]

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.check_alive')
def test_do_check_alive_active_droplets(mock_check_alive, mock_list_droplets, mock_droplets):
    """Test checking alive status for active droplets"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    mock_check_alive.return_value = True
    # Disable rolling deployment and age limit to avoid interference
    original_rolling = config["rolling_deployment"]["enabled"]
    original_age_limit = config["age_limit"]
    config["rolling_deployment"]["enabled"] = False
    config["age_limit"] = 0  # Disable age-based recycling
    
    try:
        # Execute
        result = do_check_alive()
        
        # Verify
        assert len(result) == 3
        assert "1.2.3.4" in result
        assert "5.6.7.8" in result
        assert "9.10.11.12" in result
    finally:
        config["rolling_deployment"]["enabled"] = original_rolling
        config["age_limit"] = original_age_limit
    mock_check_alive.assert_has_calls([
        call("1.2.3.4"),
        call("5.6.7.8"),
        call("9.10.11.12")
    ])

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.check_alive')
@patch('cloudproxy.providers.digitalocean.main.delete_proxy')
def test_do_check_alive_not_responding(mock_delete_proxy, mock_check_alive, mock_list_droplets, mock_droplets):
    """Test checking alive status for droplets that aren't responding"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    mock_check_alive.return_value = False
    mock_delete_proxy.return_value = True
    
    # Save original age limit
    original_age_limit = config["age_limit"]
    config["age_limit"] = 0  # Disable age-based recycling for this test
    
    try:
        # Execute
        result = do_check_alive()
        
        # Verify
        assert len(result) == 0
        # The code should only delete droplets older than 10 minutes and not responding
        # With our mock setup, that's the second and third droplets (10 minutes and 2 hours old)
        assert mock_delete_proxy.call_count == 2
        
        # Get the list of IPs that were deleted
        deleted_ips = []
        for call_args in mock_delete_proxy.call_args_list:
            args, _ = call_args
            deleted_ips.append(args[0].ip_address)
        
        # Check that the right IPs were deleted (older than 10 minutes)
        assert "5.6.7.8" in deleted_ips  # 10 minutes old
        assert "9.10.11.12" in deleted_ips  # 2 hours old
    finally:
        # Restore original age limit
        config["age_limit"] = original_age_limit

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.check_alive')
@patch('cloudproxy.providers.digitalocean.main.delete_proxy')
def test_do_check_alive_age_limit(mock_delete_proxy, mock_check_alive, mock_list_droplets, mock_droplets):
    """Test age limit recycling of droplets"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    mock_check_alive.return_value = True
    mock_delete_proxy.return_value = True
    
    # Set age limit to 1 hour and disable rolling deployment
    original_age_limit = config["age_limit"]
    original_rolling = config["rolling_deployment"]["enabled"]
    config["age_limit"] = 3600  # 1 hour in seconds
    config["rolling_deployment"]["enabled"] = False
    
    try:
        # Execute
        result = do_check_alive()
        
        # Verify - only the oldest droplet (2 hours) should be recycled
        assert len(result) == 2
        assert "1.2.3.4" in result
        assert "5.6.7.8" in result
        assert "9.10.11.12" not in result
        assert mock_delete_proxy.call_count == 1  # Only one droplet should be deleted
        
        # Check that delete_proxy was called with the third droplet
        # Don't verify the exact second parameter as implementation details might vary
        args, _ = mock_delete_proxy.call_args
        assert args[0] == mock_droplets[2]  # First parameter should be the third droplet
    finally:
        # Restore original settings
        config["age_limit"] = original_age_limit
        config["rolling_deployment"]["enabled"] = original_rolling

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.check_alive')
def test_do_check_alive_invalid_timestamp(mock_check_alive, mock_list_droplets, mock_droplets):
    """Test handling of invalid timestamps"""
    # Setup
    mock_droplets[0].created_at = "invalid-timestamp"
    mock_list_droplets.return_value = mock_droplets
    mock_check_alive.return_value = True
    # Disable rolling deployment and age limit
    original_rolling = config["rolling_deployment"]["enabled"]
    original_age_limit = config["age_limit"]
    config["rolling_deployment"]["enabled"] = False
    config["age_limit"] = 0  # Disable age-based recycling
    
    try:
        # Execute
        result = do_check_alive()
        
        # Verify
        assert len(result) == 2  # Only two valid droplets should be in the result
        assert "5.6.7.8" in result
        assert "9.10.11.12" in result
    finally:
        config["rolling_deployment"]["enabled"] = original_rolling
        config["age_limit"] = original_age_limit

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.delete_proxy')
def test_do_check_delete_empty_queue(mock_delete_proxy, mock_list_droplets, mock_droplets, setup_queues):
    """Test checking deletion when delete queue is empty"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    
    # Execute
    do_check_delete()
    
    # Verify
    mock_delete_proxy.assert_not_called()

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.delete_proxy')
def test_do_check_delete_with_ip_in_queue(mock_delete_proxy, mock_list_droplets, mock_droplets, setup_queues):
    """Test checking deletion when an IP is in the delete queue"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    mock_delete_proxy.return_value = True
    
    # Add an IP to the delete queue
    delete_queue.add("5.6.7.8")
    
    # Execute
    do_check_delete()
    
    # Verify
    assert mock_delete_proxy.call_count == 1
    # Get the droplet that was passed to delete_proxy
    args, _ = mock_delete_proxy.call_args
    assert args[0].ip_address == "5.6.7.8"  # The correct droplet was deleted
    assert "5.6.7.8" not in delete_queue  # Should be removed from queue

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.delete_proxy')
def test_do_check_delete_with_ip_in_restart_queue(mock_delete_proxy, mock_list_droplets, mock_droplets, setup_queues):
    """Test checking deletion when an IP is in the restart queue"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    mock_delete_proxy.return_value = True
    
    # Add an IP to the restart queue
    restart_queue.add("1.2.3.4")
    
    # Execute
    do_check_delete()
    
    # Verify
    assert mock_delete_proxy.call_count == 1
    # Get the droplet that was passed to delete_proxy
    args, _ = mock_delete_proxy.call_args
    assert args[0].ip_address == "1.2.3.4"  # The correct droplet was deleted
    assert "1.2.3.4" not in restart_queue  # Should be removed from queue

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.delete_proxy')
def test_do_check_delete_failed_deletion(mock_delete_proxy, mock_list_droplets, mock_droplets, setup_queues):
    """Test checking deletion when delete_proxy fails"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    mock_delete_proxy.return_value = False
    
    # Add an IP to the delete queue
    delete_queue.add("9.10.11.12")
    
    # Execute
    do_check_delete()
    
    # Verify
    assert mock_delete_proxy.call_count == 1
    # Get the droplet that was passed to delete_proxy
    args, _ = mock_delete_proxy.call_args
    assert args[0].ip_address == "9.10.11.12"  # The correct droplet was deleted
    assert "9.10.11.12" in delete_queue  # Should remain in queue as deletion failed

@patch('cloudproxy.providers.digitalocean.main.list_droplets')
@patch('cloudproxy.providers.digitalocean.main.delete_proxy')
def test_do_check_delete_exception(mock_delete_proxy, mock_list_droplets, mock_droplets, setup_queues):
    """Test checking deletion when an exception occurs"""
    # Setup
    mock_list_droplets.return_value = mock_droplets
    mock_delete_proxy.side_effect = Exception("Test exception")
    
    # Add an IP to the delete queue
    delete_queue.add("1.2.3.4")
    
    # Execute
    do_check_delete()
    
    # Verify
    assert mock_delete_proxy.call_count == 1
    # Get the droplet that was passed to delete_proxy
    args, _ = mock_delete_proxy.call_args
    assert args[0].ip_address == "1.2.3.4"  # The correct droplet was deleted
    assert "1.2.3.4" in delete_queue  # Should remain in queue as an exception occurred

@patch('cloudproxy.providers.digitalocean.main.create_firewall')
def test_do_fw_success(mock_create_firewall):
    """Test successful firewall creation"""
    # Setup
    mock_create_firewall.return_value = True
    
    # Execute
    do_fw()
    
    # Verify
    mock_create_firewall.assert_called_once()

@patch('cloudproxy.providers.digitalocean.main.create_firewall')
def test_do_fw_exists_exception(mock_create_firewall):
    """Test firewall creation when firewall already exists"""
    # Setup
    mock_create_firewall.side_effect = DOFirewallExistsException("Firewall already exists")
    
    # Execute
    do_fw()
    
    # Verify
    mock_create_firewall.assert_called_once()

@patch('cloudproxy.providers.digitalocean.main.create_firewall')
def test_do_fw_generic_exception(mock_create_firewall):
    """Test firewall creation when a generic exception occurs"""
    # Setup
    mock_create_firewall.side_effect = Exception("Test exception")
    
    # Execute
    do_fw()
    
    # Verify
    mock_create_firewall.assert_called_once()

@patch('cloudproxy.providers.digitalocean.main.do_fw')
@patch('cloudproxy.providers.digitalocean.main.do_check_delete')
@patch('cloudproxy.providers.digitalocean.main.do_check_alive')
@patch('cloudproxy.providers.digitalocean.main.do_deployment')
def test_do_start_full_process(mock_do_deployment, mock_do_check_alive, mock_do_check_delete, mock_do_fw):
    """Test the full DO start process"""
    # Setup
    mock_do_check_alive.side_effect = [["1.2.3.4"], ["1.2.3.4", "5.6.7.8"]]
    mock_do_deployment.return_value = 2
    
    # Execute
    result = do_start()
    
    # Verify
    assert mock_do_fw.call_count == 1
    assert mock_do_check_delete.call_count == 1
    assert mock_do_check_alive.call_count == 2  # Called twice
    assert mock_do_deployment.call_count == 1
    assert result == ["1.2.3.4", "5.6.7.8"]


if __name__ == "__main__":
    unittest.main()