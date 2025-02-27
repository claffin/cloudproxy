import os
import uuid
from unittest.mock import patch, MagicMock, Mock

import pytest
from azure.mgmt.compute.models import VirtualMachine, NetworkProfile, NetworkInterfaceReference
from azure.mgmt.network.models import NetworkInterface, NetworkSecurityGroup, PublicIPAddress, IPConfiguration

from cloudproxy.providers import settings
from cloudproxy.providers.azure.functions import (
    get_credentials, 
    get_compute_client, 
    get_network_client, 
    get_resource_client,
    ensure_resource_group_exists,
    create_proxy, 
    delete_proxy, 
    list_proxies
)


@pytest.fixture
def mock_settings():
    """Fixture to set up mock settings."""
    original_settings = settings.config.copy()
    
    # Set up mock Azure settings
    settings.config["providers"]["azure"]["instances"]["default"] = {
        "enabled": True,
        "ips": [],
        "scaling": {"min_scaling": 2, "max_scaling": 2},
        "size": "Standard_B1s",
        "location": "eastus",
        "secrets": {
            "subscription_id": "mock-subscription-id",
            "client_id": "mock-client-id",
            "client_secret": "mock-client-secret",
            "tenant_id": "mock-tenant-id",
            "resource_group": "mock-resource-group"
        }
    }
    
    settings.config["auth"] = {
        "username": "testuser",
        "password": "testpass"
    }
    
    yield settings.config
    
    # Restore original settings
    settings.config = original_settings


@pytest.fixture
def mock_uuid():
    """Fixture to mock UUID generation."""
    with patch('uuid.uuid4', return_value=Mock(hex='12345678901234567890123456789012')) as mock_uuid:
        yield mock_uuid


@pytest.fixture
def mock_azure_clients():
    """Fixture to mock Azure clients."""
    with patch('cloudproxy.providers.azure.functions.ClientSecretCredential') as mock_credential, \
         patch('cloudproxy.providers.azure.functions.ComputeManagementClient') as mock_compute, \
         patch('cloudproxy.providers.azure.functions.NetworkManagementClient') as mock_network, \
         patch('cloudproxy.providers.azure.functions.ResourceManagementClient') as mock_resource:
        
        # Set up mock return values
        mock_compute_client = MagicMock()
        mock_network_client = MagicMock()
        mock_resource_client = MagicMock()
        
        mock_compute.return_value = mock_compute_client
        mock_network.return_value = mock_network_client
        mock_resource.return_value = mock_resource_client
        
        # Set up common mock behaviors
        mock_resource_client.resource_groups.check_existence.return_value = True
        
        yield {
            'credential': mock_credential,
            'compute': mock_compute_client,
            'network': mock_network_client,
            'resource': mock_resource_client
        }


def test_get_credentials(mock_settings):
    """Test getting Azure credentials."""
    with patch('cloudproxy.providers.azure.functions.ClientSecretCredential') as mock_credential:
        mock_credential.return_value = "mock-credential"
        
        # Test with default instance config
        result = get_credentials()
        assert result == "mock-credential"
        mock_credential.assert_called_once_with(
            tenant_id="mock-tenant-id",
            client_id="mock-client-id",
            client_secret="mock-client-secret"
        )
        
        # Test with custom instance config
        custom_config = {
            "secrets": {
                "tenant_id": "custom-tenant-id",
                "client_id": "custom-client-id",
                "client_secret": "custom-client-secret"
            }
        }
        mock_credential.reset_mock()
        result = get_credentials(custom_config)
        assert result == "mock-credential"
        mock_credential.assert_called_once_with(
            tenant_id="custom-tenant-id",
            client_id="custom-client-id",
            client_secret="custom-client-secret"
        )


def test_get_compute_client(mock_settings):
    """Test getting Azure compute client."""
    with patch('cloudproxy.providers.azure.functions.get_credentials') as mock_get_creds, \
         patch('cloudproxy.providers.azure.functions.ComputeManagementClient') as mock_compute:
        
        mock_get_creds.return_value = "mock-credential"
        mock_compute.return_value = "mock-compute-client"
        
        # Test with default instance config
        result = get_compute_client()
        assert result == "mock-compute-client"
        mock_compute.assert_called_once_with(
            credential="mock-credential",
            subscription_id="mock-subscription-id"
        )
        
        # Test with custom instance config
        custom_config = {
            "secrets": {
                "subscription_id": "custom-subscription-id"
            }
        }
        mock_compute.reset_mock()
        mock_get_creds.reset_mock()
        mock_get_creds.return_value = "custom-credential"
        result = get_compute_client(custom_config)
        assert result == "mock-compute-client"
        mock_get_creds.assert_called_once_with(custom_config)
        mock_compute.assert_called_once_with(
            credential="custom-credential",
            subscription_id="custom-subscription-id"
        )


def test_get_network_client(mock_settings):
    """Test getting Azure network client."""
    with patch('cloudproxy.providers.azure.functions.get_credentials') as mock_get_creds, \
         patch('cloudproxy.providers.azure.functions.NetworkManagementClient') as mock_network:
        
        mock_get_creds.return_value = "mock-credential"
        mock_network.return_value = "mock-network-client"
        
        # Test with default instance config
        result = get_network_client()
        assert result == "mock-network-client"
        mock_network.assert_called_once_with(
            credential="mock-credential",
            subscription_id="mock-subscription-id"
        )


def test_get_resource_client(mock_settings):
    """Test getting Azure resource client."""
    with patch('cloudproxy.providers.azure.functions.get_credentials') as mock_get_creds, \
         patch('cloudproxy.providers.azure.functions.ResourceManagementClient') as mock_resource:
        
        mock_get_creds.return_value = "mock-credential"
        mock_resource.return_value = "mock-resource-client"
        
        # Test with default instance config
        result = get_resource_client()
        assert result == "mock-resource-client"
        mock_resource.assert_called_once_with(
            credential="mock-credential",
            subscription_id="mock-subscription-id"
        )


def test_ensure_resource_group_exists_already_exists(mock_settings, mock_azure_clients):
    """Test ensuring resource group exists when it already exists."""
    # Setup
    mock_resource_client = mock_azure_clients['resource']
    mock_resource_client.resource_groups.check_existence.return_value = True
    
    # Execute
    ensure_resource_group_exists()
    
    # Verify
    mock_resource_client.resource_groups.check_existence.assert_called_once_with("mock-resource-group")
    mock_resource_client.resource_groups.create_or_update.assert_not_called()


def test_ensure_resource_group_exists_needs_creation(mock_settings, mock_azure_clients):
    """Test ensuring resource group exists when it needs to be created."""
    # Setup
    mock_resource_client = mock_azure_clients['resource']
    mock_resource_client.resource_groups.check_existence.return_value = False
    
    # Execute
    ensure_resource_group_exists()
    
    # Verify
    mock_resource_client.resource_groups.check_existence.assert_called_once_with("mock-resource-group")
    mock_resource_client.resource_groups.create_or_update.assert_called_once_with(
        "mock-resource-group",
        {"location": "eastus"}
    )


@patch('cloudproxy.providers.azure.functions.set_auth')
def test_create_proxy_success(mock_set_auth, mock_settings, mock_azure_clients, mock_uuid):
    """Test successful creation of an Azure VM proxy."""
    # Setup
    mock_set_auth.return_value = "mock-user-data"
    mock_compute_client = mock_azure_clients['compute']
    mock_network_client = mock_azure_clients['network']
    
    # Mock the Azure resource creation results
    mock_vnet_result = MagicMock()
    mock_subnet_result = MagicMock()
    mock_subnet_result.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/virtualNetworks/vnet/subnets/subnet"
    mock_nsg_result = MagicMock()
    mock_nsg_result.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/networkSecurityGroups/nsg"
    mock_ip_result = MagicMock()
    mock_ip_result.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/ip"
    mock_nic_result = MagicMock()
    mock_nic_result.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/networkInterfaces/nic"
    
    # Set up the operation results
    mock_network_client.virtual_networks.begin_create_or_update.return_value.result.return_value = mock_vnet_result
    mock_network_client.subnets.begin_create_or_update.return_value.result.return_value = mock_subnet_result
    mock_network_client.network_security_groups.begin_create_or_update.return_value.result.return_value = mock_nsg_result
    mock_network_client.public_ip_addresses.begin_create_or_update.return_value.result.return_value = mock_ip_result
    mock_network_client.network_interfaces.begin_create_or_update.return_value.result.return_value = mock_nic_result
    
    # Execute
    result = create_proxy()
    
    # Verify
    assert result is True
    # Check that the VM creation was called with correct parameters
    mock_compute_client.virtual_machines.begin_create_or_update.assert_called_once()
    # We don't check all parameters as they are complex, but we verify the key ones
    call_args = mock_compute_client.virtual_machines.begin_create_or_update.call_args[0]
    assert call_args[0] == "mock-resource-group"
    assert "cloudproxy-default-" in call_args[1]  # Check VM name format


@patch('cloudproxy.providers.azure.functions.get_compute_client')
@patch('cloudproxy.providers.azure.functions.get_network_client')
def test_delete_proxy_success(mock_get_network, mock_get_compute, mock_settings):
    """Test successful deletion of an Azure VM proxy."""
    # Setup
    mock_compute_client = MagicMock()
    mock_network_client = MagicMock()
    mock_get_compute.return_value = mock_compute_client
    mock_get_network.return_value = mock_network_client
    
    # Mock VM object
    mock_vm = MagicMock()
    mock_vm.network_profile = MagicMock()
    mock_vm.network_profile.network_interfaces = [MagicMock()]
    mock_vm.network_profile.network_interfaces[0].id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/networkInterfaces/test-nic"
    
    # Mock NIC object
    mock_nic = MagicMock()
    mock_nic.ip_configurations = [MagicMock()]
    mock_nic.ip_configurations[0].public_ip_address = MagicMock()
    mock_nic.ip_configurations[0].public_ip_address.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/test-ip"
    mock_nic.network_security_group = MagicMock()
    mock_nic.network_security_group.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/networkSecurityGroups/test-nsg"
    
    # Set up the client methods
    mock_compute_client.virtual_machines.get.return_value = mock_vm
    mock_network_client.network_interfaces.get.return_value = mock_nic
    
    # Execute
    result = delete_proxy("test-vm")
    
    # Verify
    assert result is True
    mock_compute_client.virtual_machines.get.assert_called_once_with("mock-resource-group", "test-vm")
    mock_compute_client.virtual_machines.begin_delete.assert_called_once_with("mock-resource-group", "test-vm")
    mock_network_client.network_interfaces.get.assert_called_once_with("mock-resource-group", "test-nic")
    mock_network_client.network_interfaces.begin_delete.assert_called_once_with("mock-resource-group", "test-nic")
    mock_network_client.public_ip_addresses.begin_delete.assert_called_once_with("mock-resource-group", "test-ip")
    mock_network_client.network_security_groups.begin_delete.assert_called_once_with("mock-resource-group", "test-nsg")


@patch('cloudproxy.providers.azure.functions.get_compute_client')
@patch('cloudproxy.providers.azure.functions.get_network_client')
def test_delete_proxy_not_found(mock_get_network, mock_get_compute, mock_settings):
    """Test deletion of a non-existent Azure VM proxy."""
    # Setup
    mock_compute_client = MagicMock()
    mock_get_compute.return_value = mock_compute_client
    
    # Mock 'not found' exception
    mock_compute_client.virtual_machines.get.side_effect = Exception("ResourceNotFound")
    
    # Execute
    result = delete_proxy("test-vm")
    
    # Verify
    assert result is True  # Should return True even when VM not found
    mock_compute_client.virtual_machines.get.assert_called_once_with("mock-resource-group", "test-vm")
    mock_compute_client.virtual_machines.begin_delete.assert_not_called()


@patch('cloudproxy.providers.azure.functions.get_compute_client')
@patch('cloudproxy.providers.azure.functions.get_network_client')
def test_list_proxies(mock_get_network, mock_get_compute, mock_settings):
    """Test listing Azure VM proxies."""
    # Setup
    mock_compute_client = MagicMock()
    mock_network_client = MagicMock()
    mock_get_compute.return_value = mock_compute_client
    mock_get_network.return_value = mock_network_client
    
    # Create mock VMs with cloudproxy tags
    mock_vm1 = MagicMock()
    mock_vm1.name = "cloudproxy-default-vm1"
    mock_vm1.tags = {"type": "cloudproxy", "instance": "default"}
    mock_vm1.network_profile = MagicMock()
    mock_vm1.network_profile.network_interfaces = [MagicMock()]
    mock_vm1.network_profile.network_interfaces[0].id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/networkInterfaces/vm1-nic"
    
    mock_vm2 = MagicMock()
    mock_vm2.name = "cloudproxy-default-vm2"
    mock_vm2.tags = {"type": "cloudproxy", "instance": "default"}
    mock_vm2.network_profile = MagicMock()
    mock_vm2.network_profile.network_interfaces = [MagicMock()]
    mock_vm2.network_profile.network_interfaces[0].id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/networkInterfaces/vm2-nic"
    
    # VM with wrong tag - should not be included
    mock_vm3 = MagicMock()
    mock_vm3.name = "other-vm"
    mock_vm3.tags = {"type": "other"}
    
    # VM with different instance - should not be included for default
    mock_vm4 = MagicMock()
    mock_vm4.name = "cloudproxy-custom-vm"
    mock_vm4.tags = {"type": "cloudproxy", "instance": "custom"}
    
    # Set up mock NICs
    mock_nic1 = MagicMock()
    mock_nic1.ip_configurations = [MagicMock()]
    mock_nic1.ip_configurations[0].public_ip_address = MagicMock()
    mock_nic1.ip_configurations[0].public_ip_address.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/vm1-ip"
    
    mock_nic2 = MagicMock()
    mock_nic2.ip_configurations = [MagicMock()]
    mock_nic2.ip_configurations[0].public_ip_address = MagicMock()
    mock_nic2.ip_configurations[0].public_ip_address.id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Network/publicIPAddresses/vm2-ip"
    
    # Set up mock public IPs
    mock_ip1 = MagicMock()
    mock_ip1.ip_address = "192.168.1.1"
    
    mock_ip2 = MagicMock()
    mock_ip2.ip_address = "192.168.1.2"
    
    # Set up client responses
    mock_compute_client.virtual_machines.list.return_value = [mock_vm1, mock_vm2, mock_vm3, mock_vm4]
    
    def get_nic(resource_group, nic_name):
        if nic_name == "vm1-nic":
            return mock_nic1
        elif nic_name == "vm2-nic":
            return mock_nic2
        return None
        
    def get_ip(resource_group, ip_name):
        if ip_name == "vm1-ip":
            return mock_ip1
        elif ip_name == "vm2-ip":
            return mock_ip2
        return None
    
    mock_network_client.network_interfaces.get.side_effect = get_nic
    mock_network_client.public_ip_addresses.get.side_effect = get_ip
    
    # Execute
    result = list_proxies()
    
    # Verify
    assert len(result) == 2
    # Check that IP addresses were added to VM objects
    assert result[0].ip_address == "192.168.1.1"
    assert result[1].ip_address == "192.168.1.2" 