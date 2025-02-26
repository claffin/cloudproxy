import pytest
from unittest.mock import patch, Mock, MagicMock
import botocore
from botocore.exceptions import ClientError
import os
import sys

from cloudproxy.providers import settings
from cloudproxy.providers.aws.functions import (
    create_proxy,
    delete_proxy,
    stop_proxy,
    start_proxy,
    list_instances,
    get_clients,
    get_tags
)

# Setup fixtures
@pytest.fixture
def mock_vpc_response():
    return {'Vpcs': [{'IsDefault': True, 'VpcId': 'vpc-12345'}]}

@pytest.fixture
def mock_sg_response():
    return {'SecurityGroups': [{'GroupId': 'sg-12345'}]}

@pytest.fixture
def mock_instance():
    instance = Mock()
    instance.id = "i-12345"
    instance.public_ip_address = "1.2.3.4"
    return instance

@pytest.fixture
def mock_instances_response():
    return {
        'Reservations': [
            {
                'Instances': [
                    {
                        'InstanceId': 'i-12345',
                        'PublicIpAddress': '1.2.3.4',
                        'State': {'Name': 'running'}
                    }
                ]
            },
            {
                'Instances': [
                    {
                        'InstanceId': 'i-67890',
                        'PublicIpAddress': '5.6.7.8',
                        'State': {'Name': 'running'}
                    }
                ]
            }
        ]
    }

@pytest.fixture
def test_instance_config():
    """Create a test instance configuration"""
    return {
        "enabled": True,
        "ips": ["10.0.0.1"],
        "scaling": {"min_scaling": 2, "max_scaling": 5},
        "size": "t3.micro",
        "region": "us-west-2",
        "ami": "ami-test",
        "display_name": "Test Instance",
        "secrets": {
            "access_key_id": "test-access-key",
            "secret_access_key": "test-secret-key"
        },
        "spot": False
    }

# Test get_clients function with instance configuration
@patch('cloudproxy.providers.aws.functions.boto3.resource')
@patch('cloudproxy.providers.aws.functions.boto3.client')
def test_get_clients_with_instance_config(mock_boto3_client, mock_boto3_resource, test_instance_config):
    """Test getting AWS clients with instance-specific configuration"""
    # Setup
    mock_boto3_resource.return_value = "mock-resource"
    mock_boto3_client.return_value = "mock-client"
    
    # Execute
    ec2_resource, ec2_client = get_clients(test_instance_config)
    
    # Verify
    assert ec2_resource == "mock-resource"
    assert ec2_client == "mock-client"
    
    # Check that boto3.resource was called with correct params
    mock_boto3_resource.assert_called_once_with(
        "ec2", 
        region_name="us-west-2",
        aws_access_key_id="test-access-key",
        aws_secret_access_key="test-secret-key"
    )
    
    # Check that boto3.client was called with correct params  
    mock_boto3_client.assert_called_once_with(
        "ec2", 
        region_name="us-west-2",
        aws_access_key_id="test-access-key",
        aws_secret_access_key="test-secret-key"
    )

# Test get_tags function with instance configuration
def test_get_tags_with_instance_config(test_instance_config):
    """Test getting AWS tags with instance-specific configuration"""
    # Setup - store original config to restore later
    original_instances = settings.config["providers"]["aws"]["instances"].copy()
    
    try:
        # Add test instance to config for proper name lookup
        settings.config["providers"]["aws"]["instances"]["test-instance"] = test_instance_config
        
        # Execute
        tags, tag_specification = get_tags(test_instance_config)
        
        # Verify
        assert any(tag["Key"] == "cloudproxy" for tag in tags)
        assert any(tag["Key"] == "cloudproxy-instance" and tag["Value"] == "test-instance" for tag in tags)
        assert any(tag["Key"] == "Name" and tag["Value"] == "CloudProxy-Test Instance" for tag in tags)
        assert tag_specification[0]["ResourceType"] == "instance"
        assert tag_specification[0]["Tags"] == tags
    finally:
        # Restore original config
        settings.config["providers"]["aws"]["instances"] = original_instances

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_create_proxy_on_demand(mock_get_clients, mock_vpc_response, mock_sg_response, mock_instance):
    """Test creating an on-demand EC2 instance"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    vpc_mock = Mock()
    vpc_mock.id = "vpc-12345"
    mock_ec2.vpcs.filter.return_value = [vpc_mock]

    mock_ec2_client.describe_vpcs.return_value = mock_vpc_response
    mock_ec2_client.describe_security_groups.return_value = mock_sg_response

    # Configure the ec2 mock
    mock_ec2.create_instances.return_value = [mock_instance]

    # Save original spot setting
    original_spot = settings.config["providers"]["aws"]["instances"]["default"]["spot"]
    try:
        # Set to False for on-demand instance
        settings.config["providers"]["aws"]["instances"]["default"]["spot"] = False

        # Execute
        result = create_proxy()

        # Verify
        mock_get_clients.assert_called_once()
        mock_ec2.create_instances.assert_called_once()
        assert "InstanceMarketOptions" not in mock_ec2.create_instances.call_args[1]
        assert result == [mock_instance]
    finally:
        # Restore setting
        settings.config["providers"]["aws"]["instances"]["default"]["spot"] = original_spot

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_create_proxy_with_instance_config(mock_get_clients, mock_vpc_response, mock_sg_response, mock_instance, test_instance_config):
    """Test creating an EC2 instance with specific instance configuration"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    vpc_mock = Mock()
    vpc_mock.id = "vpc-12345"
    mock_ec2.vpcs.filter.return_value = [vpc_mock]

    mock_ec2_client.describe_vpcs.return_value = mock_vpc_response
    mock_ec2_client.describe_security_groups.return_value = mock_sg_response

    # Configure the ec2 mock
    mock_ec2.create_instances.return_value = [mock_instance]

    # Execute
    result = create_proxy(test_instance_config)

    # Verify
    mock_get_clients.assert_called_once_with(test_instance_config)
    mock_ec2.create_instances.assert_called_once()
    assert result == [mock_instance]

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_create_proxy_spot_persistent(mock_get_clients, mock_vpc_response, mock_sg_response, mock_instance):
    """Test creating a spot EC2 instance with persistent option"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    vpc_mock = Mock()
    vpc_mock.id = "vpc-12345"
    mock_ec2.vpcs.filter.return_value = [vpc_mock]

    mock_ec2_client.describe_vpcs.return_value = mock_vpc_response
    mock_ec2_client.describe_security_groups.return_value = mock_sg_response

    # Configure the ec2 mock
    mock_ec2.create_instances.return_value = [mock_instance]

    # Save original spot setting
    original_spot = settings.config["providers"]["aws"]["instances"]["default"]["spot"]
    try:
        # Set to persistent for spot instance
        settings.config["providers"]["aws"]["instances"]["default"]["spot"] = 'persistent'

        # Execute
        result = create_proxy()

        # Verify
        mock_get_clients.assert_called_once()
        mock_ec2.create_instances.assert_called_once()
        assert "InstanceMarketOptions" in mock_ec2.create_instances.call_args[1]
        market_options = mock_ec2.create_instances.call_args[1]["InstanceMarketOptions"]
        assert market_options["MarketType"] == "spot"
        assert market_options["SpotOptions"]["SpotInstanceType"] == "persistent"
        assert market_options["SpotOptions"]["InstanceInterruptionBehavior"] == "stop"
    finally:
        # Restore setting
        settings.config["providers"]["aws"]["instances"]["default"]["spot"] = original_spot

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_create_proxy_security_group_exists(mock_get_clients, mock_vpc_response, mock_sg_response, mock_instance):
    """Test creating an EC2 instance when security group already exists"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    vpc_mock = Mock()
    vpc_mock.id = "vpc-12345"
    mock_ec2.vpcs.filter.return_value = [vpc_mock]

    mock_ec2_client.describe_vpcs.return_value = mock_vpc_response
    mock_ec2_client.describe_security_groups.return_value = mock_sg_response

    # Configure sg creation to raise ClientError
    error_response = {'Error': {'Code': 'InvalidGroup.Duplicate'}}
    mock_ec2.create_security_group.side_effect = botocore.exceptions.ClientError(
        error_response, 'CreateSecurityGroup'
    )

    # Configure the ec2 mock
    mock_ec2.create_instances.return_value = [mock_instance]

    # Execute
    result = create_proxy()

    # Verify
    mock_get_clients.assert_called_once()
    mock_ec2.create_instances.assert_called_once()
    assert result == [mock_instance]

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_delete_proxy(mock_get_clients):
    """Test deleting an EC2 instance"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Create a mock for the instances collection
    instances_collection = MagicMock()
    terminated_instances = [{'InstanceId': 'i-12345', 'CurrentState': {'Name': 'shutting-down'}}]
    
    # Mock the instances collection filter method
    instances = MagicMock()
    instances.terminate.return_value = terminated_instances
    instances_collection.filter.return_value = instances
    mock_ec2.instances = instances_collection
    
    # Mock spot instance describe and cancel calls
    mock_ec2_client.describe_spot_instance_requests.return_value = {"SpotInstanceRequests": []}
    
    # Execute
    instance_id = "i-12345"
    result = delete_proxy(instance_id)
    
    # Verify
    mock_get_clients.assert_called_once()
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.terminate.assert_called_once()
    assert result == terminated_instances

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_delete_proxy_with_instance_config(mock_get_clients, test_instance_config):
    """Test deleting an EC2 instance with specific instance configuration"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Create a mock for the instances collection
    instances_collection = MagicMock()
    terminated_instances = [{'InstanceId': 'i-12345', 'CurrentState': {'Name': 'shutting-down'}}]
    
    # Mock the instances collection filter method
    instances = MagicMock()
    instances.terminate.return_value = terminated_instances
    instances_collection.filter.return_value = instances
    mock_ec2.instances = instances_collection
    
    # Mock spot instance describe and cancel calls
    mock_ec2_client.describe_spot_instance_requests.return_value = {"SpotInstanceRequests": []}
    
    # Execute
    instance_id = "i-12345"
    result = delete_proxy(instance_id, test_instance_config)
    
    # Verify
    mock_get_clients.assert_called_once_with(test_instance_config)
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.terminate.assert_called_once()
    assert result == terminated_instances

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_stop_proxy(mock_get_clients):
    """Test stopping an EC2 instance"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Create a mock for the instances collection
    instances_collection = MagicMock()
    stopped_instances = [{'InstanceId': 'i-12345', 'CurrentState': {'Name': 'stopping'}}]
    
    # Mock the instances collection filter method
    instances = MagicMock()
    instances.stop.return_value = stopped_instances
    instances_collection.filter.return_value = instances
    mock_ec2.instances = instances_collection
    
    # Execute
    instance_id = "i-12345"
    result = stop_proxy(instance_id)
    
    # Verify
    mock_get_clients.assert_called_once()
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.stop.assert_called_once()
    assert result == stopped_instances

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_stop_proxy_with_instance_config(mock_get_clients, test_instance_config):
    """Test stopping an EC2 instance with a specific instance configuration"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Create a mock for the instances collection
    instances_collection = MagicMock()
    stopped_instances = [{'InstanceId': 'i-12345', 'CurrentState': {'Name': 'stopping'}}]
    
    # Mock the instances collection filter method
    instances = MagicMock()
    instances.stop.return_value = stopped_instances
    instances_collection.filter.return_value = instances
    mock_ec2.instances = instances_collection
    
    # Execute
    instance_id = "i-12345"
    result = stop_proxy(instance_id, test_instance_config)
    
    # Verify
    mock_get_clients.assert_called_once_with(test_instance_config)
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.stop.assert_called_once()
    assert result == stopped_instances

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_start_proxy(mock_get_clients):
    """Test starting an EC2 instance"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Create a mock for the instances collection
    instances_collection = MagicMock()
    started_instances = [{'InstanceId': 'i-12345', 'CurrentState': {'Name': 'pending'}}]
    
    # Mock the instances collection filter method
    instances = MagicMock()
    instances.start.return_value = started_instances
    instances_collection.filter.return_value = instances
    mock_ec2.instances = instances_collection
    
    # Execute
    instance_id = "i-12345"
    result = start_proxy(instance_id)
    
    # Verify
    mock_get_clients.assert_called_once()
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.start.assert_called_once()
    assert result == started_instances

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_start_proxy_with_instance_config(mock_get_clients, test_instance_config):
    """Test starting an EC2 instance with specific instance configuration"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Create a mock for the instances collection
    instances_collection = MagicMock()
    started_instances = [{'InstanceId': 'i-12345', 'CurrentState': {'Name': 'pending'}}]
    
    # Mock the instances collection filter method
    instances = MagicMock()
    instances.start.return_value = started_instances
    instances_collection.filter.return_value = instances
    mock_ec2.instances = instances_collection
    
    # Execute
    instance_id = "i-12345"
    result = start_proxy(instance_id, test_instance_config)
    
    # Verify
    mock_get_clients.assert_called_once_with(test_instance_config)
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.start.assert_called_once()
    assert result == started_instances

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_list_instances(mock_get_clients, mock_instances_response):
    """Test listing EC2 instances"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Mock EC2 client's describe_instances method
    mock_ec2_client.describe_instances.return_value = mock_instances_response
    
    # Execute
    result = list_instances()
    
    # Verify
    mock_get_clients.assert_called_once()
    # The describe_instances method is called twice now - once for instances with the cloudproxy-instance tag
    # and once for legacy instances without this tag
    assert mock_ec2_client.describe_instances.call_count == 2
    assert result == mock_instances_response["Reservations"]

@patch('cloudproxy.providers.aws.functions.get_clients')
def test_list_instances_with_instance_config(mock_get_clients, mock_instances_response, test_instance_config):
    """Test listing EC2 instances with a specific instance configuration"""
    # Setup mocks
    mock_ec2 = MagicMock()
    mock_ec2_client = MagicMock()
    mock_get_clients.return_value = (mock_ec2, mock_ec2_client)
    
    # Mock EC2 client's describe_instances method
    mock_ec2_client.describe_instances.return_value = mock_instances_response
    
    # Save original config to restore later
    original_instances = settings.config["providers"]["aws"]["instances"].copy()
    
    try:
        # Add test instance to config for proper name lookup
        settings.config["providers"]["aws"]["instances"]["test-instance"] = test_instance_config
        
        # Execute
        result = list_instances(test_instance_config)
        
        # Verify
        mock_get_clients.assert_called_once_with(test_instance_config)
        mock_ec2_client.describe_instances.assert_called_once()
        
        # Check that describe_instances was called with the correct filters
        # The filter should include the cloudproxy-instance tag with value "test-instance"
        filters = mock_ec2_client.describe_instances.call_args[1]["Filters"]
        instance_tag_filter = next((f for f in filters if f["Name"] == "tag:cloudproxy-instance"), None)
        assert instance_tag_filter is not None
        assert "test-instance" in instance_tag_filter["Values"]
        
        assert result == mock_instances_response["Reservations"]
    finally:
        # Restore original config
        settings.config["providers"]["aws"]["instances"] = original_instances 