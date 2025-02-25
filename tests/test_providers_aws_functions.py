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
    list_instances
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

@patch('cloudproxy.providers.aws.functions.ec2_client')
@patch('cloudproxy.providers.aws.functions.ec2')
def test_create_proxy_on_demand(mock_ec2, mock_ec2_client, mock_vpc_response, mock_sg_response, mock_instance):
    """Test creating an on-demand EC2 instance"""
    # Setup mocks
    vpc_mock = Mock()
    vpc_mock.id = "vpc-12345"
    mock_ec2.vpcs.filter.return_value = [vpc_mock]
    
    mock_ec2_client.describe_vpcs.return_value = mock_vpc_response
    mock_ec2_client.describe_security_groups.return_value = mock_sg_response
    
    # Configure the ec2 mock
    mock_ec2.create_instances.return_value = [mock_instance]
    
    # Save original spot setting
    original_spot = settings.config["providers"]["aws"]["spot"]
    try:
        # Set to False for on-demand instance
        settings.config["providers"]["aws"]["spot"] = False

        # Execute
        result = create_proxy()

        # Verify
        mock_ec2.create_instances.assert_called_once()
        assert "InstanceMarketOptions" not in mock_ec2.create_instances.call_args[1]
        assert result == [mock_instance]  # The function returns the instance list
    finally:
        # Restore original setting
        settings.config["providers"]["aws"]["spot"] = original_spot

@patch('cloudproxy.providers.aws.functions.ec2_client')
@patch('cloudproxy.providers.aws.functions.ec2')
def test_create_proxy_spot_persistent(mock_ec2, mock_ec2_client, mock_vpc_response, mock_sg_response, mock_instance):
    """Test creating a spot EC2 instance with persistent option"""
    # Setup mocks
    vpc_mock = Mock()
    vpc_mock.id = "vpc-12345"
    mock_ec2.vpcs.filter.return_value = [vpc_mock]
    
    mock_ec2_client.describe_vpcs.return_value = mock_vpc_response
    mock_ec2_client.describe_security_groups.return_value = mock_sg_response
    
    # Configure the ec2 mock
    mock_ec2.create_instances.return_value = [mock_instance]
    
    # Save original spot setting
    original_spot = settings.config["providers"]["aws"]["spot"]
    try:
        # Set to persistent for spot instance
        settings.config["providers"]["aws"]["spot"] = 'persistent'

        # Execute
        result = create_proxy()

        # Verify
        mock_ec2.create_instances.assert_called_once()
        assert "InstanceMarketOptions" in mock_ec2.create_instances.call_args[1]
        assert mock_ec2.create_instances.call_args[1]["InstanceMarketOptions"]["MarketType"] == "spot"
        assert mock_ec2.create_instances.call_args[1]["InstanceMarketOptions"]["SpotOptions"]["SpotInstanceType"] == "persistent"
        assert result == [mock_instance]  # The function returns the instance list
    finally:
        # Restore original setting
        settings.config["providers"]["aws"]["spot"] = original_spot

@patch('cloudproxy.providers.aws.functions.ec2_client')
@patch('cloudproxy.providers.aws.functions.ec2')
def test_create_proxy_security_group_exists(mock_ec2, mock_ec2_client, mock_vpc_response, mock_sg_response, mock_instance):
    """Test creating a proxy when security group already exists"""
    # Setup mocks
    vpc_mock = Mock()
    vpc_mock.id = "vpc-12345"
    mock_ec2.vpcs.filter.return_value = [vpc_mock]
    
    mock_ec2_client.describe_vpcs.return_value = mock_vpc_response
    mock_ec2_client.describe_security_groups.return_value = mock_sg_response
    
    # Make create_security_group raise ClientError
    mock_ec2.create_security_group.side_effect = ClientError(
        {'Error': {'Code': 'InvalidGroup.Duplicate', 'Message': 'Security group already exists'}},
        'CreateSecurityGroup'
    )
    
    # Configure the ec2 mock for instance creation
    mock_ec2.create_instances.return_value = [mock_instance]
    
    # Save original spot setting
    original_spot = settings.config["providers"]["aws"]["spot"]
    try:
        # Set to False for on-demand instance
        settings.config["providers"]["aws"]["spot"] = False

        # Execute
        result = create_proxy()

        # Verify
        mock_ec2.create_instances.assert_called_once()
        assert result == [mock_instance]  # The function returns the instance list
    finally:
        # Restore original setting
        settings.config["providers"]["aws"]["spot"] = original_spot

@patch('cloudproxy.providers.aws.functions.ec2_client')
@patch('cloudproxy.providers.aws.functions.ec2')
def test_delete_proxy(mock_ec2, mock_ec2_client):
    """Test deleting an EC2 instance"""
    # Setup - Create a mock for the instances collection
    instances_collection = MagicMock()
    terminated_instances = [{'InstanceId': 'i-12345', 'CurrentState': {'Name': 'shutting-down'}}]
    
    # Mock the instances collection filter method
    instances = MagicMock()
    instances.terminate.return_value = terminated_instances
    instances_collection.filter.return_value = instances
    mock_ec2.instances = instances_collection
    
    # Mock spot instance describe and cancel calls
    mock_ec2_client.describe_spot_instance_requests.return_value = {"SpotInstanceRequests": []}
    
    # Save original spot setting
    original_spot = settings.config["providers"]["aws"]["spot"]
    try:
        # Set to False for regular instance
        settings.config["providers"]["aws"]["spot"] = False
        
        # Execute
        instance_id = "i-12345"
        result = delete_proxy(instance_id)
        
        # Verify
        instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
        instances.terminate.assert_called_once()
        assert result == terminated_instances
    finally:
        # Restore setting
        settings.config["providers"]["aws"]["spot"] = original_spot

@patch('cloudproxy.providers.aws.functions.ec2')
def test_stop_proxy(mock_ec2):
    """Test stopping an EC2 instance"""
    # Setup - Create a mock for the instances collection
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
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.stop.assert_called_once()
    assert result == stopped_instances

@patch('cloudproxy.providers.aws.functions.ec2')
def test_start_proxy(mock_ec2):
    """Test starting an EC2 instance"""
    # Setup - Create a mock for the instances collection
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
    instances_collection.filter.assert_called_once_with(InstanceIds=[instance_id])
    instances.start.assert_called_once()
    assert result == started_instances

@patch('cloudproxy.providers.aws.functions.ec2_client')
def test_list_instances(mock_ec2_client, mock_instances_response):
    """Test listing EC2 instances"""
    # Setup
    mock_ec2_client.describe_instances.return_value = mock_instances_response
    
    # Execute
    result = list_instances()
    
    # Verify
    mock_ec2_client.describe_instances.assert_called_once()
    assert len(result) == 2
    assert result[0]['Instances'][0]['InstanceId'] == 'i-12345'
    assert result[1]['Instances'][0]['InstanceId'] == 'i-67890' 