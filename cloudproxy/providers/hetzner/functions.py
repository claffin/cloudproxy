import os
import uuid

from hcloud import Client
from hcloud.images.domain import Image
from hcloud.server_types.domain import ServerType
from hcloud.datacenters.domain import Datacenter
from hcloud.locations.domain import Location
from loguru import logger

from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth
from cloudproxy.credentials import credential_manager

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# Module-level variables for clients (kept for potential future use or specific test setups, but not used by get_client for caching)
# client = None

def reset_clients():
    """
    Reset any module-level state if necessary (e.g., for testing).
    For the current get_client implementation, this function does nothing.
    """
    # global client # If we were caching client here per instance_id
    # client = {}
    pass

def get_client(instance_id: str):
    """
    Get a Hetzner client for the specific instance configuration using CredentialManager.
    Always creates a new client for the specific instance ID.
    
    Args:
        instance_id: The ID of the instance configuration
        
    Returns:
        Client: Hetzner client instance for the configuration, or None if credentials not found or invalid
    """
    # Do NOT use module-level global variables for caching clients here.
    # Each call gets a client specific to the instance_id.

    if credential_manager is None:
        logger.error("CredentialManager not initialized in hetzner.functions.get_client")
        return None

    secrets = credential_manager.get_credentials("hetzner", instance_id)

    if not secrets or "access_token" not in secrets:
        # logger.debug(f"No Hetzner credentials or access_token found for instance '{instance_id}'.")
        return None
    
    # Always create a new Hetzner client for this specific call
    try:
        # Create Hetzner client using the instance-specific credentials
        local_client = Client(token=secrets["access_token"])
        return local_client
    except Exception as e:
        logger.error(f"Error creating Hetzner client for {instance_id}: {e}")
        return None


def create_proxy(instance_config=None, instance_id="default"):
    """
    Create a Hetzner proxy server.

    Args:
        instance_config: The specific instance configuration
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["hetzner"]["instances"].get(instance_id, settings.config["providers"]["hetzner"]["instances"]["default"])

    # Get instance-specific client
    hetzner_client = get_client(instance_id)

    if hetzner_client is None:
        logger.warning(f"No Hetzner credentials found for instance '{instance_id}'. Cannot create server.")
        return None

    # Prepare user data script
    user_data = set_auth(settings.config["auth"]["username"], settings.config["auth"]["password"])

    # Determine location or datacenter parameter
    datacenter = instance_config.get("datacenter", None)
    location = instance_config.get("location", None)

    # Create the server with instance-specific settings
    response = hetzner_client.servers.create(
        name=f"cloudproxy-{instance_id}-{str(uuid.uuid4())}",
        server_type=ServerType(instance_config["size"]),
        image=Image(name="ubuntu-20.04"),
        user_data=user_data,
        datacenter=Datacenter(name=datacenter) if datacenter else None,
        location=Location(name=location) if location else None,
        labels={"type": "cloudproxy", "instance": instance_id}
    )

    return response


def delete_proxy(server_id, instance_config=None, instance_id="default"):
    """
    Delete a Hetzner proxy server.
    
    Args:
        server_id: ID of the server to delete
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["hetzner"]["instances"].get(instance_id, settings.config["providers"]["hetzner"]["instances"]["default"])
        
    hetzner_client = get_client(instance_id)

    if hetzner_client is None:
        logger.warning(f"No Hetzner credentials found for instance '{instance_id}'. Cannot delete server.")
        return False

    try:
        # Handle both ID and Server object
        server_obj = None
        server_identifier = None
        
        if hasattr(server_id, 'id'):
            # It's a server object
            server_obj = server_id
            server_identifier = server_id.id
        else:
            # It's an ID, we need to get the server first
            server_identifier = server_id
            try:
                server_obj = hetzner_client.servers.get_by_id(server_id)
            except Exception as e:
                # If server not found, consider it already deleted
                if "not found" in str(e).lower() or "404" in str(e) or "does not exist" in str(e).lower():
                    logger.info(f"Hetzner server with ID {server_id} not found for instance '{instance_id}', considering it already deleted")
                    return True
                # Re-raise other errors
                raise
        
        # If we got the server object successfully, delete it
        if server_obj:
            logger.info(f"Deleting Hetzner server with ID: {server_identifier} for instance '{instance_id}'")
            response = server_obj.delete()
            logger.info(f"Hetzner deletion API call completed with response: {response}")
            return response
        else:
            # This should not happen since we either return earlier or have a server object
            logger.warning(f"No valid Hetzner server object found for ID: {server_identifier} for instance '{instance_id}'")
            return True
            
    except Exception as e:
        # If the server is not found or any other error occurs
        # during deletion, consider it already deleted
        if "not found" in str(e).lower() or "404" in str(e) or "attribute" in str(e).lower() or "does not exist" in str(e).lower():
            logger.info(f"Exception during Hetzner server deletion for instance '{instance_id}' indicates it's already gone: {str(e)}")
            return True
        else:
            # Re-raise other errors
            logger.error(f"Error during Hetzner server deletion for instance '{instance_id}': {str(e)}")
            raise


def list_proxies(instance_config=None, instance_id="default"):
    """
    List Hetzner proxy servers for a specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
        
    Returns:
        list: List of Hetzner servers
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["hetzner"]["instances"].get(instance_id, settings.config["providers"]["hetzner"]["instances"]["default"])
        
    hetzner_client = get_client(instance_id)

    if hetzner_client is None:
        logger.warning(f"No Hetzner credentials found for instance '{instance_id}'. Cannot list servers.")
        return []
    
    # Filter servers by labels
    label_selector = "type=cloudproxy"
    if instance_id != "default":
        label_selector += f",instance={instance_id}"
        
    servers = hetzner_client.servers.get_all(label_selector=label_selector)
    
    # For default instance, also include servers created before multi-instance support
    if instance_id == "default":
        # Get old servers without instance label but with cloudproxy type
        old_servers = hetzner_client.servers.get_all(label_selector="type=cloudproxy")
        # Filter out servers that have instance labels
        old_servers = [s for s in old_servers if "instance" not in s.labels]
        # Merge lists, avoiding duplicates
        existing_ids = {s.id for s in servers}
        servers.extend([s for s in old_servers if s.id not in existing_ids])
    
    return servers
