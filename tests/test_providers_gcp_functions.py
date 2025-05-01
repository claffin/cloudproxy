import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import json
import uuid
import googleapiclient.errors

# Import mock definitions first
@pytest.fixture(autouse=True)
def mock_gcp_environment():
    """
    Mock GCP environment for all tests in this module.
    This fixture sets up the mocks for the module-level objects in cloudproxy.providers.gcp.functions
    before any tests are run.
    """
    # Create a mock module with the necessary components
    mock_compute = MagicMock()
    
    # Create a patch to replace 'compute' when it's accessed at the module level
    with patch.dict('sys.modules', {"cloudproxy.providers.gcp.functions": sys.modules["cloudproxy.providers.gcp.functions"]}):
        sys.modules["cloudproxy.providers.gcp.functions"].compute = mock_compute
        
        yield mock_compute
        
        # Cleanup: remove the mock after the test
        if hasattr(sys.modules["cloudproxy.providers.gcp.functions"], "compute"):
            delattr(sys.modules["cloudproxy.providers.gcp.functions"], "compute")

# Now import the functions that use the mocked module
from cloudproxy.providers.gcp.functions import (
    create_proxy, 
    delete_proxy, 
    stop_proxy, 
    start_proxy, 
    list_instances
)
from cloudproxy.providers.settings import config

@patch('uuid.uuid4')
def test_create_proxy(mock_uuid, mock_gcp_environment):
    """Test create_proxy function"""
    # Setup
    mock_uuid.return_value = "test-uuid"
    
    # Set up the mocks for this specific test
    mock_compute = mock_gcp_environment
    images_mock = MagicMock()
    mock_compute.images.return_value = images_mock
    get_from_family_mock = MagicMock()
    images_mock.getFromFamily.return_value = get_from_family_mock
    get_from_family_mock.execute.return_value = {"selfLink": "projects/debian-cloud/global/images/debian-10-buster-v20220719"}
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    insert_mock = MagicMock()
    instances_mock.insert.return_value = insert_mock
    insert_mock.execute.return_value = {"name": "cloudproxy-123"}
    
    # Execute
    result = create_proxy()
    
    # Verify
    assert mock_compute.instances().insert.called
    assert result == {"name": "cloudproxy-123"}
    
    # Check arguments
    _, kwargs = mock_compute.instances().insert.call_args
    assert kwargs["project"] == config["providers"]["gcp"]["project"]
    assert kwargs["zone"] == config["providers"]["gcp"]["zone"]
    
    # Check body
    body = kwargs["body"]
    assert "cloudproxy-" in body["name"]
    assert body["machineType"].endswith(config["providers"]["gcp"]["size"])
    assert "cloudproxy" in body["tags"]["items"]
    assert body["labels"]["cloudproxy"] == "cloudproxy"
    assert body["disks"][0]["boot"] is True
    assert body["networkInterfaces"][0]["accessConfigs"][0]["type"] == "ONE_TO_ONE_NAT"
    assert "startup-script" in body["metadata"]["items"][0]["key"]

def test_delete_proxy_success(mock_gcp_environment):
    """Test delete_proxy function successful case"""
    # Setup
    mock_compute = mock_gcp_environment
    name = "cloudproxy-123"
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    delete_mock = MagicMock()
    instances_mock.delete.return_value = delete_mock
    delete_mock.execute.return_value = {"status": "RUNNING"}
    
    # Execute
    result = delete_proxy(name)
    
    # Verify
    mock_compute.instances().delete.assert_called_with(
        project=config["providers"]["gcp"]["project"],
        zone=config["providers"]["gcp"]["zone"],
        instance=name
    )
    assert result == {"status": "RUNNING"}

def test_delete_proxy_http_error(mock_gcp_environment):
    """Test delete_proxy function when HTTP error occurs"""
    # Setup
    mock_compute = mock_gcp_environment
    name = "cloudproxy-123"
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    http_error = googleapiclient.errors.HttpError(
        resp=Mock(status=404), 
        content=b'Instance not found'
    )
    instances_mock.delete.side_effect = http_error
    
    # Execute
    result = delete_proxy(name)
    
    # Verify
    assert result is None

def test_stop_proxy_success(mock_gcp_environment):
    """Test stop_proxy function successful case"""
    # Setup
    mock_compute = mock_gcp_environment
    name = "cloudproxy-123"
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    stop_mock = MagicMock()
    instances_mock.stop.return_value = stop_mock
    stop_mock.execute.return_value = {"status": "STOPPING"}
    
    # Execute
    result = stop_proxy(name)
    
    # Verify
    mock_compute.instances().stop.assert_called_with(
        project=config["providers"]["gcp"]["project"],
        zone=config["providers"]["gcp"]["zone"],
        instance=name
    )
    assert result == {"status": "STOPPING"}

def test_stop_proxy_http_error(mock_gcp_environment):
    """Test stop_proxy function when HTTP error occurs"""
    # Setup
    mock_compute = mock_gcp_environment
    name = "cloudproxy-123"
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    http_error = googleapiclient.errors.HttpError(
        resp=Mock(status=404), 
        content=b'Instance not found'
    )
    instances_mock.stop.side_effect = http_error
    
    # Execute
    result = stop_proxy(name)
    
    # Verify
    assert result is None

def test_start_proxy_success(mock_gcp_environment):
    """Test start_proxy function successful case"""
    # Setup
    mock_compute = mock_gcp_environment
    name = "cloudproxy-123"
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    start_mock = MagicMock()
    instances_mock.start.return_value = start_mock
    start_mock.execute.return_value = {"status": "RUNNING"}
    
    # Execute
    result = start_proxy(name)
    
    # Verify
    mock_compute.instances().start.assert_called_with(
        project=config["providers"]["gcp"]["project"],
        zone=config["providers"]["gcp"]["zone"],
        instance=name
    )
    assert result == {"status": "RUNNING"}

def test_start_proxy_http_error(mock_gcp_environment):
    """Test start_proxy function when HTTP error occurs"""
    # Setup
    mock_compute = mock_gcp_environment
    name = "cloudproxy-123"
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    http_error = googleapiclient.errors.HttpError(
        resp=Mock(status=404), 
        content=b'Instance not found'
    )
    instances_mock.start.side_effect = http_error
    
    # Execute
    result = start_proxy(name)
    
    # Verify
    assert result is None

def test_list_instances_with_instances(mock_gcp_environment):
    """Test list_instances function when instances exist"""
    # Setup
    mock_compute = mock_gcp_environment
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    list_mock = MagicMock()
    instances_mock.list.return_value = list_mock
    list_mock.execute.return_value = {
        "items": [
            {
                "name": "cloudproxy-123",
                "networkInterfaces": [{"accessConfigs": [{"natIP": "1.2.3.4"}]}],
                "status": "RUNNING"
            }
        ]
    }
    
    # Execute
    result = list_instances()
    
    # Verify
    mock_compute.instances().list.assert_called_with(
        project=config["providers"]["gcp"]["project"],
        zone=config["providers"]["gcp"]["zone"],
        filter='labels.cloudproxy eq cloudproxy'
    )
    assert len(result) == 1
    assert result[0]["name"] == "cloudproxy-123"

def test_list_instances_no_instances(mock_gcp_environment):
    """Test list_instances function when no instances exist"""
    # Setup
    mock_compute = mock_gcp_environment
    
    instances_mock = MagicMock()
    mock_compute.instances.return_value = instances_mock
    list_mock = MagicMock()
    instances_mock.list.return_value = list_mock
    list_mock.execute.return_value = {}
    
    # Execute
    result = list_instances()
    
    # Verify
    assert result == [] 