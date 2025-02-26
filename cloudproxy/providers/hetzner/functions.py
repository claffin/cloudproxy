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

# Initialize client with default instance configuration
client = Client(token=settings.config["providers"]["hetzner"]["instances"]["default"]["secrets"]["access_token"])
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# Remove this invalid logger configuration
# logger = logging.getLogger(__name__)
# loguru logger is already imported above


def get_client(instance_config=None):
    """
    Get a Hetzner client for the specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        Client: Hetzner client instance for the configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["hetzner"]["instances"]["default"]
    
    return Client(token=instance_config["secrets"]["access_token"])


def create_proxy(instance_config=None):
    """
    Create a Hetzner proxy server.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["hetzner"]["instances"]["default"]
        
    # Get instance name for labeling
    instance_id = next(
        (name for name, inst in settings.config["providers"]["hetzner"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    # Get instance-specific client
    hetzner_client = get_client(instance_config)
    
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


def delete_proxy(server_id, instance_config=None):
    """
    Delete a Hetzner proxy server.
    
    Args:
        server_id: ID of the server to delete
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["hetzner"]["instances"]["default"]
        
    # Get instance-specific client
    hetzner_client = get_client(instance_config)
    
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
                    logger.info(f"Hetzner server with ID {server_id} not found, considering it already deleted")
                    return True
                # Re-raise other errors
                raise
        
        # If we got the server object successfully, delete it
        if server_obj:
            logger.info(f"Deleting Hetzner server with ID: {server_identifier}")
            response = server_obj.delete()
            logger.info(f"Hetzner deletion API call completed with response: {response}")
            return response
        else:
            # This should not happen since we either return earlier or have a server object
            logger.warning(f"No valid Hetzner server object found for ID: {server_identifier}")
            return True
            
    except Exception as e:
        # If the server is not found or any other error occurs
        # during deletion, consider it already deleted
        if "not found" in str(e).lower() or "404" in str(e) or "attribute" in str(e).lower() or "does not exist" in str(e).lower():
            logger.info(f"Exception during Hetzner server deletion indicates it's already gone: {str(e)}")
            return True
        else:
            # Re-raise other errors
            logger.error(f"Error during Hetzner server deletion: {str(e)}")
            raise


def list_proxies(instance_config=None):
    """
    List Hetzner proxy servers.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        list: List of Hetzner servers
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["hetzner"]["instances"]["default"]
        
    # Get instance name for filtering
    instance_id = next(
        (name for name, inst in settings.config["providers"]["hetzner"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    # Get instance-specific client
    hetzner_client = get_client(instance_config)
    
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
