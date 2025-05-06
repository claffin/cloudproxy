import pytest
from unittest.mock import patch, Mock, ANY
import datetime
from datetime import timezone
import itertools

from cloudproxy.providers.gcp.main import (
    gcp_deployment,
    gcp_check_alive,
    gcp_check_delete,
    gcp_check_stop,
    gcp_start
)
from cloudproxy.providers.settings import delete_queue, restart_queue, config

# Setup fixtures
@pytest.fixture
def setup_instances():
    """Setup test instances and restore original state after test"""
    # Save original values
    original_delete_queue = delete_queue.copy()
    original_restart_queue = restart_queue.copy()

    # Calculate a creation time that's just a few seconds ago to avoid age limit recycling
    just_now = datetime.datetime.now(timezone.utc)
    just_now_str = just_now.strftime('%Y-%m-%dT%H:%M:%S.%f%z')

    # Create test instances
    running_instance = {
        "name": "instance-1",
        "networkInterfaces": [{"accessConfigs": [{"natIP": "1.2.3.4"}]}],
        "status": "RUNNING",
        "creationTimestamp": just_now_str
    }

    terminated_instance = {
        "name": "instance-2",
        "networkInterfaces": [{"accessConfigs": [{"natIP": "5.6.7.8"}]}],
        "status": "TERMINATED",
        "creationTimestamp": just_now_str
    }
    
    stopping_instance = {
        "name": "instance-3",
        "networkInterfaces": [{"accessConfigs": [{"natIP": "9.10.11.12"}]}],
        "status": "STOPPING",
        "creationTimestamp": just_now_str
    }

    provisioning_instance = {
        "name": "instance-4",
        "networkInterfaces": [{"accessConfigs": [{"natIP": "13.14.15.16"}]}],
        "status": "PROVISIONING",
        "creationTimestamp": just_now_str
    }
    
    staging_instance = {
        "name": "instance-5",
        "networkInterfaces": [{"accessConfigs": [{"natIP": "17.18.19.20"}]}],
        "status": "STAGING",
        "creationTimestamp": just_now_str
    }

    instances = [running_instance, terminated_instance, stopping_instance, provisioning_instance, staging_instance]

    yield instances

    # Restore original state
    delete_queue.clear()
    delete_queue.update(original_delete_queue)
    restart_queue.clear()
    restart_queue.update(original_restart_queue)

@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.create_proxy')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
def test_gcp_deployment_scale_up(mock_delete_proxy, mock_create_proxy, mock_list_instances, setup_instances):
    """Test scaling up GCP instances"""
    # Setup - Only 2 instances (running and terminated), need to scale up to 4
    mock_list_instances.return_value = [setup_instances[0], setup_instances[1]]
    mock_create_proxy.return_value = True

    # Execute
    min_scaling = 4
    result = gcp_deployment(min_scaling)

    # Verify
    assert mock_create_proxy.call_count == 2  # Should create 2 new instances
    assert mock_delete_proxy.call_count == 0  # Should not delete any
    assert result == 2  # Returns number of instances after deployment

@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.create_proxy')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
def test_gcp_deployment_scale_down(mock_delete_proxy, mock_create_proxy, mock_list_instances, setup_instances):
    """Test scaling down GCP instances"""
    # Setup - 3 instances (running, terminated, stopping), need to scale down to 1
    mock_list_instances.return_value = [setup_instances[0], setup_instances[1], setup_instances[2]]
    mock_delete_proxy.return_value = True

    # Execute
    min_scaling = 1
    result = gcp_deployment(min_scaling)

    # Verify
    assert mock_delete_proxy.call_count == 2  # Should delete 2 instances
    assert mock_create_proxy.call_count == 0  # Should not create any
    assert result == 3  # Returns number of instances after deployment

@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.create_proxy')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
def test_gcp_deployment_no_change(mock_delete_proxy, mock_create_proxy, mock_list_instances, setup_instances):
    """Test when no scaling change is needed"""
    # Setup - 2 instances (running and terminated), need to keep 2
    mock_list_instances.return_value = [setup_instances[0], setup_instances[1]]

    # Execute
    min_scaling = 2
    result = gcp_deployment(min_scaling)

    # Verify
    assert mock_delete_proxy.call_count == 0  # Should not delete any
    assert mock_create_proxy.call_count == 0  # Should not create any
    assert result == 2  # Returns number of instances

@patch('cloudproxy.providers.gcp.main.check_alive')
@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
@patch('cloudproxy.providers.gcp.main.start_proxy')
def test_gcp_check_alive_running(mock_start_proxy, mock_delete_proxy, mock_list_instances, mock_check_alive, setup_instances):
    """Test checking alive for running instances"""
    # Setup
    mock_list_instances.return_value = [setup_instances[0]] # Just the running instance
    mock_check_alive.return_value = True

    # Execute
    result = gcp_check_alive()

    # Verify
    assert "1.2.3.4" in result
    assert mock_delete_proxy.call_count == 0
    assert mock_start_proxy.call_count == 0

@patch('cloudproxy.providers.gcp.main.check_alive')
@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
@patch('cloudproxy.providers.gcp.main.start_proxy')
def test_gcp_check_alive_terminated(mock_start_proxy, mock_delete_proxy, mock_list_instances, mock_check_alive, setup_instances):
    """Test checking alive for terminated instances"""
    # Setup
    mock_list_instances.return_value = [setup_instances[1]] # Just the terminated instance
    mock_start_proxy.return_value = True
    mock_check_alive.return_value = False # Instance not reachable yet since we just started it

    # Execute
    result = gcp_check_alive()

    # Verify
    mock_start_proxy.call_count == 1 # Should start the terminated instance
    assert mock_delete_proxy.call_count == 0
    assert len(result) == 0 # No IPs ready yet as instance was just started

@patch('cloudproxy.providers.gcp.main.check_alive')
@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
@patch('cloudproxy.providers.gcp.main.start_proxy')
def test_gcp_check_alive_stopping(mock_start_proxy, mock_delete_proxy, mock_list_instances, mock_check_alive, setup_instances):
    """Test checking alive for stopping instances"""
    # Setup
    mock_list_instances.return_value = [setup_instances[2]] # Just the stopping instance
    mock_check_alive.return_value = False

    # Execute
    result = gcp_check_alive()

    # Verify
    assert mock_start_proxy.call_count == 0
    assert mock_delete_proxy.call_count == 0
    assert len(result) == 0

@patch('cloudproxy.providers.gcp.main.check_alive')
@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
@patch('cloudproxy.providers.gcp.main.start_proxy')
def test_gcp_check_alive_provisioning_staging(mock_start_proxy, mock_delete_proxy, mock_list_instances, mock_check_alive, setup_instances):
    """Test checking alive for provisioning/staging instances"""
    # Setup
    mock_list_instances.return_value = [setup_instances[3], setup_instances[4]] # Provisioning and Staging instances
    mock_check_alive.return_value = False

    # Execute
    result = gcp_check_alive()

    # Verify
    assert mock_start_proxy.call_count == 0
    assert mock_delete_proxy.call_count == 0
    assert len(result) == 0

@patch('cloudproxy.providers.gcp.main.check_alive')
@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
@patch('cloudproxy.providers.gcp.main.start_proxy')
def test_gcp_check_alive_not_alive_too_long(mock_start_proxy, mock_delete_proxy, mock_list_instances, mock_check_alive, setup_instances):
    """Test checking alive for instances not alive for too long"""
    # Setup
    # Create a mock instance with a creation time far in the past (more than 10 minutes)
    old_time = datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=15)
    old_time_str = old_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    old_instance = {
        "name": "old-instance",
        "networkInterfaces": [{"accessConfigs": [{"natIP": "21.22.23.24"}]}],
        "status": "RUNNING",
        "creationTimestamp": old_time_str
    }
    mock_list_instances.return_value = [old_instance]
    mock_check_alive.return_value = False # Instance is not alive
    mock_delete_proxy.return_value = True

    # Execute
    result = gcp_check_alive()

    # Verify
    assert mock_delete_proxy.call_count == 1 # Should delete the instance
    assert len(result) == 0
    mock_delete_proxy.assert_called_once_with("old-instance", instance_id="default")


@patch('cloudproxy.providers.gcp.main.check_alive')
@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
@patch('cloudproxy.providers.gcp.main.start_proxy')
def test_gcp_check_alive_age_limit_exceeded(mock_start_proxy, mock_delete_proxy, mock_list_instances, mock_check_alive, setup_instances):
    """Test checking alive for instances exceeding age limit"""
    # Save original age limit value
    original_age_limit = config["age_limit"]

    try:
        # Set age limit to a small value to make instances expire quickly
        config["age_limit"] = 60  # 60 seconds

        # Create a mock instance with a creation time far in the past
        old_time = datetime.datetime.now(timezone.utc) - datetime.timedelta(seconds=120)
        old_time_str = old_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        old_instance = {
            "name": "old-instance-age",
            "networkInterfaces": [{"accessConfigs": [{"natIP": "25.26.27.28"}]}],
            "status": "RUNNING",
            "creationTimestamp": old_time_str
        }
        mock_list_instances.return_value = [old_instance]
        mock_check_alive.return_value = True # Instance is alive but old
        mock_delete_proxy.return_value = True

        # Execute
        result = gcp_check_alive()

        # Verify
        assert mock_delete_proxy.call_count == 1 # Should delete the instance
        assert len(result) == 0
        mock_delete_proxy.assert_called_once_with("old-instance-age", instance_id="default")
    finally:
        # Restore original age limit
        config["age_limit"] = original_age_limit

@patch('cloudproxy.providers.gcp.main.check_alive')
@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
@patch('cloudproxy.providers.gcp.main.start_proxy')
def test_gcp_check_alive_type_key_error(mock_start_proxy, mock_delete_proxy, mock_list_instances, mock_check_alive):
    """Test handling TypeError/KeyError in gcp_check_alive"""
    # Setup with an instance missing required keys
    invalid_instance = {
        "name": "invalid-instance",
        "networkInterfaces": [{}], # Missing accessConfigs
        "status": "RUNNING",
        "creationTimestamp": "2023-01-01T00:00:00.000Z"
    }
    mock_list_instances.return_value = [invalid_instance]
    mock_check_alive.return_value = False

    # Execute
    result = gcp_check_alive()

    # Verify
    assert mock_start_proxy.call_count == 0
    assert mock_delete_proxy.call_count == 0
    assert len(result) == 0 # No IPs should be added

@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.delete_proxy')
def test_gcp_check_delete(mock_delete_proxy, mock_list_instances, setup_instances):
    """Test checking for instances to delete"""
    # Setup
    mock_list_instances.return_value = [setup_instances[0]] # Just the running instance
    mock_delete_proxy.return_value = True
    delete_queue.add("1.2.3.4") # Add IP to delete queue

    # Execute
    gcp_check_delete()

    # Verify
    assert mock_delete_proxy.call_count == 1 # Should delete the instance in delete queue
    assert "1.2.3.4" not in delete_queue # IP should be removed from queue
    mock_delete_proxy.assert_called_once_with("instance-1", instance_id="default")


@patch('cloudproxy.providers.gcp.main.list_instances')
@patch('cloudproxy.providers.gcp.main.stop_proxy')
def test_gcp_check_stop(mock_stop_proxy, mock_list_instances, setup_instances):
    """Test checking for instances to stop"""
    # Setup
    mock_list_instances.return_value = [setup_instances[0]] # Just the running instance
    mock_stop_proxy.return_value = True
    restart_queue.add("1.2.3.4") # Add IP to restart queue

    # Execute
    gcp_check_stop()

    # Verify
    assert mock_stop_proxy.call_count == 1 # Should stop the instance in restart queue
    assert "1.2.3.4" not in restart_queue # IP should be removed from queue
    mock_stop_proxy.assert_called_once_with("instance-1", instance_id="default")


@patch('cloudproxy.providers.gcp.main.gcp_check_delete')
@patch('cloudproxy.providers.gcp.main.gcp_check_stop')
@patch('cloudproxy.providers.gcp.main.gcp_check_alive')
@patch('cloudproxy.providers.gcp.main.gcp_deployment')
def test_gcp_start(mock_gcp_deployment, mock_gcp_check_alive, mock_gcp_check_stop, mock_gcp_check_delete):
    """Test the main gcp_start function"""
    # Setup
    mock_gcp_check_alive.return_value = ["1.2.3.4", "5.6.7.8"]
    original_min_scaling = config["providers"]["gcp"]["scaling"]["min_scaling"]

    try:
        # Set test scaling
        config["providers"]["gcp"]["scaling"]["min_scaling"] = 3

        # Execute
        result = gcp_start()

        # Verify
        # We need to get the instance_config that gcp_start would use
        expected_instance_config = config["providers"]["gcp"]["instances"]["default"]
        
        mock_gcp_check_delete.assert_called_once_with(expected_instance_config, instance_id="default")
        mock_gcp_check_stop.assert_called_once_with(expected_instance_config, instance_id="default")
        mock_gcp_deployment.assert_called_once_with(3, expected_instance_config, instance_id="default")
        mock_gcp_check_alive.assert_called_once_with(expected_instance_config, instance_id="default")

        assert result == ["1.2.3.4", "5.6.7.8"] # Should return IPs from check_alive
    finally:
        # Restore setting
        config["providers"]["gcp"]["scaling"]["min_scaling"] = original_min_scaling
