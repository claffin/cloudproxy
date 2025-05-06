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

# Import mock definitions first

@patch('uuid.uuid4')
@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_create_proxy(mock_get_compute_client, mock_uuid):
    """Test create_proxy function"""
    # Setup
    mock_uuid.return_value = "test-uuid"

    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    images_mock = MagicMock()
    mock_compute_client.images.return_value = images_mock
    get_from_family_mock = MagicMock()
    images_mock.getFromFamily.return_value = get_from_family_mock
    get_from_family_mock.execute.return_value = {"selfLink": "projects/debian-cloud/global/images/debian-10-buster-v20220719"}

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    insert_mock = MagicMock()
    instances_mock.insert.return_value = insert_mock
    insert_mock.execute.return_value = {"name": "cloudproxy-123"}

    instance_config = {
        "project": "test-project",
        "zone": "test-zone",
        "size": "n1-standard-1",
        "image_project": "debian-cloud",
        "image_family": "debian-10"
    }

    # Execute
    result = create_proxy(instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    assert mock_compute_client.instances().insert.called
    assert result == {"name": "cloudproxy-123"}

    # Check arguments
    _, kwargs = mock_compute_client.instances().insert.call_args
    assert kwargs["project"] == instance_config["project"]
    assert kwargs["zone"] == instance_config["zone"]

    # Check body
    body = kwargs["body"]
    assert "cloudproxy-" in body["name"]
    assert body["machineType"].endswith(instance_config["size"])
    assert "cloudproxy" in body["tags"]["items"]
    assert body["labels"]["cloudproxy"] == "cloudproxy"
    assert body["disks"][0]["boot"] is True
    assert body["networkInterfaces"][0]["accessConfigs"][0]["type"] == "ONE_TO_ONE_NAT"
    assert "startup-script" in body["metadata"]["items"][0]["key"]

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_delete_proxy_success(mock_get_compute_client):
    """Test delete_proxy function successful case"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    name = "cloudproxy-123"

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    delete_mock = MagicMock()
    instances_mock.delete.return_value = delete_mock
    delete_mock.execute.return_value = {"status": "RUNNING"}

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = delete_proxy(name, instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    mock_compute_client.instances().delete.assert_called_with(
        project=instance_config["project"],
        zone=instance_config["zone"],
        instance=name
    )
    assert result == {"status": "RUNNING"}

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_delete_proxy_http_error(mock_get_compute_client):
    """Test delete_proxy function when HTTP error occurs"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    name = "cloudproxy-123"

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    http_error = googleapiclient.errors.HttpError(
        resp=Mock(status=404),
        content=b'Instance not found'
    )
    instances_mock.delete.side_effect = http_error

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = delete_proxy(name, instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    assert result is None

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_stop_proxy_success(mock_get_compute_client):
    """Test stop_proxy function successful case"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    name = "cloudproxy-123"

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    stop_mock = MagicMock()
    instances_mock.stop.return_value = stop_mock
    stop_mock.execute.return_value = {"status": "STOPPING"}

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = stop_proxy(name, instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    mock_compute_client.instances().stop.assert_called_with(
        project=instance_config["project"],
        zone=instance_config["zone"],
        instance=name
    )
    assert result == {"status": "STOPPING"}

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_stop_proxy_http_error(mock_get_compute_client):
    """Test stop_proxy function when HTTP error occurs"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    name = "cloudproxy-123"

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    http_error = googleapiclient.errors.HttpError(
        resp=Mock(status=404),
        content=b'Instance not found'
    )
    instances_mock.stop.side_effect = http_error

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = stop_proxy(name, instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    assert result is None

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_start_proxy_success(mock_get_compute_client):
    """Test start_proxy function successful case"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    name = "cloudproxy-123"

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    start_mock = MagicMock()
    instances_mock.start.return_value = start_mock
    start_mock.execute.return_value = {"status": "RUNNING"}

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = start_proxy(name, instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    mock_compute_client.instances().start.assert_called_with(
        project=instance_config["project"],
        zone=instance_config["zone"],
        instance=name
    )
    assert result == {"status": "RUNNING"}

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_start_proxy_http_error(mock_get_compute_client):
    """Test start_proxy function when HTTP error occurs"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    name = "cloudproxy-123"

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    http_error = googleapiclient.errors.HttpError(
        resp=Mock(status=404),
        content=b'Instance not found'
    )
    instances_mock.start.side_effect = http_error

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = start_proxy(name, instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    assert result is None

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_list_instances_with_instances(mock_get_compute_client):
    """Test list_instances function when instances exist"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
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

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = list_instances(instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    mock_compute_client.instances().list.assert_called_with(
        project=instance_config["project"],
        zone=instance_config["zone"],
        filter='labels.cloudproxy eq cloudproxy'
    )
    assert len(result) == 1
    assert result[0]["name"] == "cloudproxy-123"

@patch('cloudproxy.providers.gcp.functions.get_compute_client')
def test_list_instances_no_instances(mock_get_compute_client):
    """Test list_instances function when no instances exist"""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute_client.return_value = mock_compute_client

    instances_mock = MagicMock()
    mock_compute_client.instances.return_value = instances_mock
    list_mock = MagicMock()
    instances_mock.list.return_value = list_mock
    list_mock.execute.return_value = {}

    instance_config = {
        "project": "test-project",
        "zone": "test-zone"
    }

    # Execute
    result = list_instances(instance_config=instance_config, instance_id="test-instance")

    # Verify
    mock_get_compute_client.assert_called_once_with("test-instance")
    assert result == []