import os

import digitalocean
import uuid as uuid
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth

# Initialize manager with default instance configuration
manager = digitalocean.Manager(
    token=settings.config["providers"]["digitalocean"]["instances"]["default"]["secrets"]["access_token"]
)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# Get default token
token = settings.config["providers"]["digitalocean"]["instances"]["default"]["secrets"]["access_token"]

class DOFirewallExistsException(Exception):
    pass

def get_manager(instance_config=None):
    """
    Get a DigitalOcean manager for the specific instance configuration.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        digitalocean.Manager: Manager instance for the configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["digitalocean"]["instances"]["default"]
    
    return digitalocean.Manager(token=instance_config["secrets"]["access_token"])

def create_proxy(instance_config=None):
    """
    Create a DigitalOcean proxy droplet.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["digitalocean"]["instances"]["default"]
    
    # Get instance name for tagging
    instance_id = next(
        (name for name, inst in settings.config["providers"]["digitalocean"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    user_data = set_auth(
        settings.config["auth"]["username"], settings.config["auth"]["password"]
    )
    
    # Create droplet with instance-specific settings
    do_manager = get_manager(instance_config)
    droplet = digitalocean.Droplet(
        token=instance_config["secrets"]["access_token"],
        name=f"cloudproxy-{instance_id}-{str(uuid.uuid1())}",
        region=instance_config["region"],
        image="ubuntu-20-04-x64",
        size_slug=instance_config["size"],
        backups=False,
        user_data=user_data,
        tags=["cloudproxy", f"cloudproxy-{instance_id}"],
    )
    droplet.create()
    return True


def delete_proxy(droplet_id, instance_config=None):
    """
    Delete a DigitalOcean proxy droplet.
    
    Args:
        droplet_id: ID of the droplet to delete
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["digitalocean"]["instances"]["default"]
    
    # Use instance-specific token
    try:
        # Handle both ID and Droplet object
        if hasattr(droplet_id, 'id'):
            # Get a fresh reference to the droplet to ensure we have the latest state
            do_manager = get_manager(instance_config)
            try:
                droplet = do_manager.get_droplet(droplet_id.id)
                logger.info(f"Found droplet with ID: {droplet_id.id} - executing deletion")
            except Exception as e:
                # If we can't get the droplet, it might already be deleted
                if "not found" in str(e).lower() or "404" in str(e).lower():
                    logger.info(f"Droplet with ID {droplet_id.id} not found, considering it already deleted")
                    return True
                raise  # Re-raise other errors
                
            # Now delete the droplet
            deleted = droplet.destroy()
            logger.info(f"DigitalOcean deletion API call completed with result: {deleted}")
            return deleted
        else:
            # It's just an ID, not an object
            do_manager = get_manager(instance_config)
            try:
                droplet = do_manager.get_droplet(droplet_id)
                logger.info(f"Found droplet with ID: {droplet_id} - executing deletion")
            except Exception as e:
                # If we can't get the droplet, it might already be deleted
                if "not found" in str(e).lower() or "404" in str(e).lower():
                    logger.info(f"Droplet with ID {droplet_id} not found, considering it already deleted")
                    return True
                raise  # Re-raise other errors
                
            # Now delete the droplet
            deleted = droplet.destroy()
            logger.info(f"DigitalOcean deletion API call completed with result: {deleted}")
            return deleted
    except Exception as e:
        # Log the error but don't fail if the droplet is already gone
        if "not found" in str(e).lower() or "404" in str(e).lower():
            # Droplet is already gone, consider it successfully deleted
            logger.info(f"Droplet deletion exception indicates it's already gone: {str(e)}")
            return True
        else:
            # Re-raise other errors
            logger.error(f"Error during droplet deletion: {str(e)}")
            raise


def list_droplets(instance_config=None):
    """
    List DigitalOcean proxy droplets.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        list: List of droplets
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["digitalocean"]["instances"]["default"]
    
    # Get instance name for tagging
    instance_id = next(
        (name for name, inst in settings.config["providers"]["digitalocean"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    # Get instance-specific droplets by tag
    do_manager = get_manager(instance_config)
    
    # First try with instance-specific tag
    my_droplets = do_manager.get_all_droplets(tag_name=f"cloudproxy-{instance_id}")
    
    # If this is the default instance, also get droplets created before multi-instance support
    if instance_id == "default":
        # Get old droplets with just the cloudproxy tag (created before multi-instance support)
        old_droplets = do_manager.get_all_droplets(tag_name="cloudproxy")
        
        # Only add droplets that don't have the new instance-specific tag
        if old_droplets:
            existing_ids = {d.id for d in my_droplets}
            for droplet in old_droplets:
                # Check if this droplet has any instance-specific tags
                has_instance_tag = False
                for tag in droplet.tags:
                    if tag.startswith("cloudproxy-") and tag != "cloudproxy":
                        has_instance_tag = True
                        break
                
                # If no instance tag and not already in our list, add it
                if not has_instance_tag and droplet.id not in existing_ids:
                    my_droplets.append(droplet)
    
    return my_droplets

def create_firewall(instance_config=None):
    """
    Create a DigitalOcean firewall for proxy droplets.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["digitalocean"]["instances"]["default"]
    
    # Get instance name for firewall naming
    instance_id = next(
        (name for name, inst in settings.config["providers"]["digitalocean"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    fw = digitalocean.Firewall(
            token=instance_config["secrets"]["access_token"],
            name=f"cloudproxy-{instance_id}",
            inbound_rules=__create_inbound_fw_rules(),
            outbound_rules=__create_outbound_fw_rules(),
            tags=[f"cloudproxy-{instance_id}"]
         )
    try:
        fw.create()
    except digitalocean.DataReadError as dre:
        if dre.args[0] == 'duplicate name':
            raise DOFirewallExistsException(f"Firewall already exists for 'cloudproxy-{instance_id}'")
        else:
            raise

def __create_inbound_fw_rules():
    return [
        digitalocean.InboundRule(
            protocol="tcp", 
            ports="8899", 
            sources=digitalocean.Sources(addresses=[
                            "0.0.0.0/0",
                            "::/0"]
                        )
            )
    ]

def __create_outbound_fw_rules():
    return [
        digitalocean.OutboundRule(
            protocol="tcp",
            ports="all",
            destinations=digitalocean.Destinations(addresses=[
                            "0.0.0.0/0",
                            "::/0"]
                        )
            ),
        digitalocean.OutboundRule(
            protocol="udp",
            ports="all",
            destinations=digitalocean.Destinations(addresses=[
                            "0.0.0.0/0",
                            "::/0"]
                        )
            )
    ]
