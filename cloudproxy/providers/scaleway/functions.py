import os
import json
from scaleway.apis import ComputeAPI

from cloudproxy.providers.config import set_auth
from cloudproxy.providers.settings import config

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# Module-level variables needed for tests
compute_api = None

def reset_clients():
    """
    Reset the module-level client variables.
    This is primarily used in tests to ensure a clean state.
    """
    global compute_api
    compute_api = None

def get_client(instance_config=None):
    """
    Initialize and return Scaleway client based on the provided configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        ComputeAPI: Scaleway compute API client
    """
    # Use global variable to allow mocking in tests
    global compute_api
    
    # If client is already set (likely by a test), return it
    if compute_api is not None:
        return compute_api
        
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
    
    # Get Scaleway credentials from the instance configuration
    auth_token = instance_config["secrets"]["auth_token"]
    region = instance_config["region"]
    
    # Create Scaleway client using the instance-specific credentials
    compute_api = ComputeAPI(auth_token=auth_token, region=region)
    
    return compute_api

def create_proxy(instance_config=None):
    """
    Create a Scaleway proxy instance.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        dict: The created instance details
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
    
    # Get client
    api = get_client(instance_config)
    
    # Setup user data with appropriate authentication
    # user_data = set_auth(config["auth"]["username"], config["auth"]["password"])
    
    # Use instance_name if available
    instance_name = instance_config.get("display_name", "default")
    instance_id = next(
        (name for name, inst in config["providers"]["scaleway"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    # Prepare the instance creation data following Scaleway API requirements
    instance_data = {
        "name": f"CloudProxy-{instance_name}",
        "commercial_type": instance_config["size"], # Revert to commercial_type
        "image": "3f1b9623-71ba-4fe3-b994-27fcdaa850ba", # Keep hardcoded image
        "tags": ["cloudproxy", f"cloudproxy-instance-{instance_id}"],
        "project": instance_config.get("organization", None), # Assume Org ID = Project ID for now
        "enable_ipv6": False,
        "boot_type": "local",
        # Temporarily remove user_data to simplify the request
        # "user_data": {
        #     "cloud-init": user_data
        # }
    }
    
    # Create the server
    response = api.query().servers.post({"server": instance_data})
    server_id = response['server']['id']
    
    # Power on the server
    api.query().servers(server_id).action.post({"action": "poweron"})
    
    return response['server']

def delete_proxy(instance_id, instance_config=None):
    """
    Delete a Scaleway proxy instance.
    
    Args:
        instance_id: ID of the instance to delete
        instance_config: The specific instance configuration
        
    Returns:
        bool: True if successfully deleted
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
    
    # Get client
    api = get_client(instance_config)
    
    try:
        # Terminate the server
        api.query().servers(instance_id).action.post({"action": "terminate"})
        return True
    except Exception as e:
        return False

def stop_proxy(instance_id, instance_config=None):
    """
    Stop a Scaleway proxy instance.
    
    Args:
        instance_id: ID of the instance to stop
        instance_config: The specific instance configuration
        
    Returns:
        bool: True if successfully stopped
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
    
    # Get client
    api = get_client(instance_config)
    
    try:
        # Stop the server
        api.query().servers(instance_id).action.post({"action": "poweroff"})
        return True
    except Exception as e:
        return False

def start_proxy(instance_id, instance_config=None):
    """
    Start a Scaleway proxy instance.
    
    Args:
        instance_id: ID of the instance to start
        instance_config: The specific instance configuration
        
    Returns:
        bool: True if successfully started
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
    
    # Get client
    api = get_client(instance_config)
    
    try:
        # Start the server
        api.query().servers(instance_id).action.post({"action": "poweron"})
        return True
    except Exception as e:
        return False

def list_instances(instance_config=None):
    """
    List all Scaleway instances that match the cloudproxy tags.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        list: List of instances
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
    
    # Get client
    api = get_client(instance_config)
    
    # Get instance name for filtering
    instance_id = next(
        (name for name, inst in config["providers"]["scaleway"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    try:
        # Get all servers
        response = api.query().servers.get()
        servers = response.get('servers', [])
        
        # Filter servers by tags
        filtered_servers = []
        for server in servers:
            if 'tags' in server and 'cloudproxy' in server['tags'] and f'cloudproxy-instance-{instance_id}' in server['tags']:
                filtered_servers.append(server)
        
        return filtered_servers
    except Exception as e:
        return [] 