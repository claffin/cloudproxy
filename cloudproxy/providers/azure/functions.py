import os
import uuid
import secrets
import string

from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from loguru import logger

from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def get_credentials(instance_config=None):
    """
    Get Azure credentials for the specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        ClientSecretCredential: Credential object for Azure authentication
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    return ClientSecretCredential(
        tenant_id=instance_config["secrets"]["tenant_id"],
        client_id=instance_config["secrets"]["client_id"],
        client_secret=instance_config["secrets"]["client_secret"]
    )


def get_compute_client(instance_config=None):
    """
    Get Azure Compute client for the specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        ComputeManagementClient: Client for Azure Compute operations
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    credentials = get_credentials(instance_config)
    return ComputeManagementClient(
        credential=credentials,
        subscription_id=instance_config["secrets"]["subscription_id"]
    )


def get_network_client(instance_config=None):
    """
    Get Azure Network client for the specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        NetworkManagementClient: Client for Azure Network operations
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    credentials = get_credentials(instance_config)
    return NetworkManagementClient(
        credential=credentials,
        subscription_id=instance_config["secrets"]["subscription_id"]
    )


def get_resource_client(instance_config=None):
    """
    Get Azure Resource client for the specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        ResourceManagementClient: Client for Azure Resource operations
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    credentials = get_credentials(instance_config)
    return ResourceManagementClient(
        credential=credentials,
        subscription_id=instance_config["secrets"]["subscription_id"]
    )


def ensure_resource_group_exists(instance_config=None):
    """
    Ensure the resource group exists, create if it doesn't.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    resource_client = get_resource_client(instance_config)
    resource_group_name = instance_config["secrets"]["resource_group"]
    location = instance_config["location"]
    
    # Check if resource group exists
    if resource_client.resource_groups.check_existence(resource_group_name):
        logger.info(f"Resource group {resource_group_name} already exists")
    else:
        # Create resource group
        logger.info(f"Creating resource group {resource_group_name} in {location}")
        resource_client.resource_groups.create_or_update(
            resource_group_name,
            {"location": location}
        )
        logger.info(f"Resource group {resource_group_name} created successfully")


def create_proxy(instance_config=None):
    """
    Create an Azure VM for proxying.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    # Get instance name for labeling
    instance_id = next(
        (name for name, inst in settings.config["providers"]["azure"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    # Get instance-specific clients
    compute_client = get_compute_client(instance_config)
    network_client = get_network_client(instance_config)
    
    # Ensure resource group exists
    ensure_resource_group_exists(instance_config)
    
    resource_group = instance_config["secrets"]["resource_group"]
    location = instance_config["location"]
    vm_size = instance_config["size"]
    
    # Generate unique name for VM and its resources
    unique_id = str(uuid.uuid4())[:8]
    vm_name = f"cloudproxy-{instance_id}-{unique_id}"
    vnet_name = f"{vm_name}-vnet"
    subnet_name = f"{vm_name}-subnet"
    ip_name = f"{vm_name}-ip"
    nic_name = f"{vm_name}-nic"
    nsg_name = f"{vm_name}-nsg"
    
    # Prepare cloud-init script
    user_data = set_auth(settings.config["auth"]["username"], settings.config["auth"]["password"])
    
    try:
        # 1. Create Virtual Network
        logger.info(f"Creating Virtual Network {vnet_name}")
        vnet_params = {
            "location": location,
            "address_space": {
                "address_prefixes": ["10.0.0.0/16"]
            }
        }
        network_client.virtual_networks.begin_create_or_update(
            resource_group,
            vnet_name,
            vnet_params
        ).result()
        
        # 2. Create Subnet
        logger.info(f"Creating Subnet {subnet_name}")
        subnet_params = {
            "address_prefix": "10.0.0.0/24"
        }
        subnet = network_client.subnets.begin_create_or_update(
            resource_group,
            vnet_name,
            subnet_name,
            subnet_params
        ).result()
        
        # 3. Create Network Security Group
        logger.info(f"Creating Network Security Group {nsg_name}")
        nsg_params = {
            "location": location,
            "security_rules": [
                {
                    "name": "Allow-SSH",
                    "properties": {
                        "protocol": "Tcp",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "destinationPortRange": "22",
                        "sourcePortRange": "*",
                        "priority": 100,
                        "direction": "Inbound"
                    }
                },
                {
                    "name": "Allow-Proxy",
                    "properties": {
                        "protocol": "Tcp",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "destinationPortRange": "8899",
                        "sourcePortRange": "*",
                        "priority": 110,
                        "direction": "Inbound"
                    }
                }
            ]
        }
        nsg = network_client.network_security_groups.begin_create_or_update(
            resource_group,
            nsg_name,
            nsg_params
        ).result()
        
        # 4. Create Public IP
        logger.info(f"Creating Public IP {ip_name}")
        ip_params = {
            "location": location,
            "sku": {"name": "Standard"},
            "public_ip_allocation_method": "Static",
            "public_ip_address_version": "IPV4"
        }
        public_ip = network_client.public_ip_addresses.begin_create_or_update(
            resource_group,
            ip_name,
            ip_params
        ).result()
        
        # 5. Create Network Interface
        logger.info(f"Creating Network Interface {nic_name}")
        nic_params = {
            "location": location,
            "ip_configurations": [
                {
                    "name": f"{vm_name}-ipconfig",
                    "subnet": {"id": subnet.id},
                    "public_ip_address": {"id": public_ip.id}
                }
            ],
            "network_security_group": {"id": nsg.id}
        }
        nic = network_client.network_interfaces.begin_create_or_update(
            resource_group,
            nic_name,
            nic_params
        ).result()
        
        # 6. Create VM
        logger.info(f"Creating Virtual Machine {vm_name}")
        # Generate a secure password for the admin user
        admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(16))
        
        vm_params = {
            "location": location,
            "tags": {"type": "cloudproxy", "instance": instance_id},
            "os_profile": {
                "computer_name": vm_name,
                "admin_username": "azureuser",
                "admin_password": admin_password,
                "custom_data": user_data
            },
            "hardware_profile": {
                "vm_size": vm_size
            },
            "storage_profile": {
                "image_reference": {
                    "publisher": "Canonical",
                    "offer": "0001-com-ubuntu-server-focal",
                    "sku": "20_04-lts-gen2",
                    "version": "latest"
                },
                "os_disk": {
                    "name": f"{vm_name}-disk",
                    "caching": "ReadWrite",
                    "create_option": "FromImage",
                    "managed_disk": {
                        "storage_account_type": "Standard_LRS"
                    }
                }
            },
            "network_profile": {
                "network_interfaces": [
                    {
                        "id": nic.id,
                        "primary": True
                    }
                ]
            },
            "os_profile_linux_config": {
                "disable_password_authentication": True,
                "ssh": {
                    "public_keys": [
                        {
                            "path": "/home/azureuser/.ssh/authorized_keys",
                            "key_data": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+wWK73dCr+jgQOAxNsHAnNNNMEMWOHYEccp6wJm2gotpr9katuF/ZAdou5AaW1C61slRkHRkpRRX9FA9CYBiitZgvCCz+3nWNN7l/Up54Zps/pHWGZLHNJZRYyAB6j5yVLMVHIHriY49d/GZTZVR8tQ2h9Ge7ZcwbVtcQGyE5WG4RJ2M0hBXk4gzQT3cMxpxswHCoXdz9f9mvoS/PMG/qNf9HfwDgToGp9CvYSx3Nd9X4+Ozk+T/EAZCN3iXN87B32nanRrMjYK3m7Su9IPtiUJBbDWVbKNjk5SgQ2Y9Gpxp3yWOLJtXNsK5yamzwOdKO+CdDIoJxDjjqj5ZN cloudproxy"
                        }
                    ]
                }
            }
        }
        
        compute_client.virtual_machines.begin_create_or_update(
            resource_group,
            vm_name,
            vm_params
        ).result()
        
        logger.info(f"VM {vm_name} created successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error creating VM: {e}")
        raise


def delete_proxy(vm_or_id, instance_config=None):
    """
    Delete an Azure VM.
    
    Args:
        vm_or_id: VM object or ID of the VM to delete
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    compute_client = get_compute_client(instance_config)
    network_client = get_network_client(instance_config)
    resource_group = instance_config["secrets"]["resource_group"]
    
    # Get resource name
    vm_name = None
    if isinstance(vm_or_id, str) and "/" in vm_or_id:
        # It's a resource ID
        vm_name = vm_or_id.split("/")[-1]
    elif isinstance(vm_or_id, str):
        # It's a VM name
        vm_name = vm_or_id
    else:
        # It's a VM object
        vm_name = vm_or_id.name if hasattr(vm_or_id, 'name') else None
        
    if not vm_name:
        logger.error("Cannot determine VM name")
        return False
    
    try:
        # Get VM to confirm it exists and to get network interface
        logger.info(f"Getting VM {vm_name} details")
        try:
            vm = compute_client.virtual_machines.get(resource_group, vm_name)
        except Exception as e:
            if "not found" in str(e).lower() or "ResourceNotFound" in str(e):
                logger.info(f"VM {vm_name} not found, considering it already deleted")
                return True
            raise
            
        # Get network interface IDs
        network_interfaces = []
        if vm.network_profile and vm.network_profile.network_interfaces:
            for nic_ref in vm.network_profile.network_interfaces:
                network_interfaces.append(nic_ref.id.split('/')[-1])
        
        # Now delete the VM
        logger.info(f"Deleting VM {vm_name}")
        compute_client.virtual_machines.begin_delete(resource_group, vm_name).result()
        logger.info(f"VM {vm_name} deleted successfully")
        
        # Delete NIC and its associated public IP
        for nic_name in network_interfaces:
            try:
                logger.info(f"Getting Network Interface {nic_name} details")
                nic = network_client.network_interfaces.get(resource_group, nic_name)
                
                # Get public IP from NIC
                public_ip_ids = []
                if nic.ip_configurations:
                    for ip_config in nic.ip_configurations:
                        if ip_config.public_ip_address and ip_config.public_ip_address.id:
                            public_ip_ids.append(ip_config.public_ip_address.id.split('/')[-1])
                
                # Get NSG from NIC
                nsg_id = None
                if nic.network_security_group and nic.network_security_group.id:
                    nsg_id = nic.network_security_group.id.split('/')[-1]
                
                # Delete NIC
                logger.info(f"Deleting Network Interface {nic_name}")
                network_client.network_interfaces.begin_delete(resource_group, nic_name).result()
                logger.info(f"Network Interface {nic_name} deleted successfully")
                
                # Delete associated resources
                for public_ip_name in public_ip_ids:
                    logger.info(f"Deleting Public IP {public_ip_name}")
                    network_client.public_ip_addresses.begin_delete(resource_group, public_ip_name).result()
                    logger.info(f"Public IP {public_ip_name} deleted successfully")
                
                if nsg_id:
                    logger.info(f"Deleting Network Security Group {nsg_id}")
                    network_client.network_security_groups.begin_delete(resource_group, nsg_id).result()
                    logger.info(f"Network Security Group {nsg_id} deleted successfully")
                    
            except Exception as e:
                logger.error(f"Error deleting resources for NIC {nic_name}: {e}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error deleting VM {vm_name}: {e}")
        # If VM not found, consider it already deleted
        if "not found" in str(e).lower() or "ResourceNotFound" in str(e):
            logger.info(f"VM {vm_name} not found during deletion, considering it already deleted")
            return True
        raise


def list_proxies(instance_config=None):
    """
    List Azure VMs used as proxies.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        list: List of Azure VMs
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["azure"]["instances"]["default"]
    
    # Get instance name for filtering
    instance_id = next(
        (name for name, inst in settings.config["providers"]["azure"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    compute_client = get_compute_client(instance_config)
    network_client = get_network_client(instance_config)
    resource_group = instance_config["secrets"]["resource_group"]
    
    # Get all VMs in the resource group
    proxies = []
    for vm in compute_client.virtual_machines.list(resource_group):
        # Check if this is a cloudproxy VM for this instance
        if vm.tags and vm.tags.get('type') == 'cloudproxy':
            # For default instance, include old VMs without instance tag
            if instance_id == "default" and 'instance' not in vm.tags:
                proxies.append(vm)
            # For any instance, match the instance tag
            elif vm.tags.get('instance') == instance_id:
                proxies.append(vm)
    
    # Enrich VM objects with their IP addresses
    for proxy in proxies:
        # Get network interfaces
        if proxy.network_profile and proxy.network_profile.network_interfaces:
            for nic_ref in proxy.network_profile.network_interfaces:
                nic_name = nic_ref.id.split('/')[-1]
                nic = network_client.network_interfaces.get(resource_group, nic_name)
                
                # Get public IP address
                if nic.ip_configurations:
                    for ip_config in nic.ip_configurations:
                        if ip_config.public_ip_address:
                            ip_name = ip_config.public_ip_address.id.split('/')[-1]
                            public_ip = network_client.public_ip_addresses.get(resource_group, ip_name)
                            proxy.ip_address = public_ip.ip_address
    
    return proxies 