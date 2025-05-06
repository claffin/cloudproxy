import os

import digitalocean
import uuid as uuid
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers import settings
from cloudproxy.providers.config import set_auth
from cloudproxy.credentials import credential_manager
 
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
 
# Module-level variables for clients (kept for potential future use or specific test setups, but not used by get_manager for caching)
# manager = None

class DOFirewallExistsException(Exception):
    pass

def reset_clients():
    """
    Reset any module-level state if necessary (e.g., for testing).
    For the current get_manager implementation, this function does nothing.
    """
    # global manager # If we were caching manager here per instance_id
    # manager = {} 
    pass

def get_manager(instance_id: str):
    """
    Get a DigitalOcean manager for the specific instance configuration using CredentialManager.
    Always creates a new manager for the specific instance ID.
    
    Args:
        instance_id: The ID of the instance configuration
        
    Returns:
        digitalocean.Manager: Manager instance for the configuration, or None if credentials not found or invalid
    """
    # Do NOT use module-level global variables for caching clients here.
    # Each call gets a manager specific to the instance_id.

    if credential_manager is None:
        logger.error("CredentialManager not initialized in digitalocean.functions.get_manager")
        return None

    secrets = credential_manager.get_credentials("digitalocean", instance_id)

    if not secrets or "access_token" not in secrets:
        # logger.debug(f"No DigitalOcean credentials or access_token found for instance '{instance_id}'.")
        return None
    
    # Always create a new DigitalOcean manager for this specific call
    try:
        # Create DigitalOcean manager using the instance-specific credentials
        local_manager = digitalocean.Manager(token=secrets["access_token"])
        return local_manager
    except Exception as e:
        logger.error(f"Error creating DigitalOcean manager for {instance_id}: {e}")
        return None

def create_proxy(instance_config=None, instance_id="default"):
    """
    Create a DigitalOcean proxy droplet.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        # If no specific config is passed, use the one for the given instance_id
        instance_config = settings.config["providers"]["digitalocean"]["instances"].get(instance_id, settings.config["providers"]["digitalocean"]["instances"]["default"])
    # else, instance_id might be re-derived if instance_config was passed directly.
    # For consistency, if instance_config is passed, we should ideally also have the matching instance_id.
    # The original logic for deriving instance_id if instance_config is passed:
    if instance_config != settings.config["providers"]["digitalocean"]["instances"].get(instance_id):
        instance_id = next(
            (name for name, inst in settings.config["providers"]["digitalocean"]["instances"].items()
             if inst == instance_config),
            instance_id # Keep original instance_id if config not found by object comparison
        )

    user_data = set_auth(
        settings.config["auth"]["username"], settings.config["auth"]["password"]
    )
    
    # Create droplet with instance-specific settings
    # Get manager using the determined/passed instance_id
    do_manager = get_manager(instance_id=instance_id)
    
    if do_manager is None:
        logger.warning(f"No DigitalOcean credentials found for instance '{instance_id}'. Cannot create droplet.")
        return False

    # We should use the token from the manager/credentials, not directly from instance_config if it can be avoided
    # However, digitalocean.Droplet requires a token directly.
    # Ensure instance_config has the secrets.
    current_secrets = credential_manager.get_credentials("digitalocean", instance_id)
    if not current_secrets or "access_token" not in current_secrets:
        logger.error(f"Access token not found in CredentialManager for DO instance {instance_id} during create_proxy.")
        return False

    droplet = digitalocean.Droplet(
        token=current_secrets["access_token"], # Use token from CredentialManager
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


def delete_proxy(droplet_id, instance_config=None, instance_id="default"):
    """
    Delete a DigitalOcean proxy droplet.
    
    Args:
        droplet_id: ID of the droplet to delete
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["digitalocean"]["instances"].get(instance_id, settings.config["providers"]["digitalocean"]["instances"]["default"])
    
    do_manager = get_manager(instance_id=instance_id)

    if do_manager is None:
        logger.warning(f"No DigitalOcean credentials found for instance '{instance_id}'. Cannot delete droplet.")
        return False

    try:
        # Handle both ID and Droplet object
        if hasattr(droplet_id, 'id'):
            # Get a fresh reference to the droplet to ensure we have the latest state
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


def list_droplets(instance_config=None, instance_id="default"):
    """
    List DigitalOcean proxy droplets.
    
    Args:
        instance_config: The specific instance configuration
        
    Returns:
        list: List of droplets
    """
    if instance_config is None:
        # If no specific config is passed, use the one for the given instance_id
        instance_config = settings.config["providers"]["digitalocean"]["instances"].get(instance_id, settings.config["providers"]["digitalocean"]["instances"]["default"])
    # else, instance_id might be re-derived if instance_config was passed directly.
    if instance_config != settings.config["providers"]["digitalocean"]["instances"].get(instance_id):
        instance_id = next(
            (name for name, inst in settings.config["providers"]["digitalocean"]["instances"].items()
             if inst == instance_config),
            instance_id
        )
    
    # Get instance-specific droplets by tag
    # Get manager using the determined/passed instance_id
    do_manager = get_manager(instance_id=instance_id)
    
    if do_manager is None:
        logger.warning(f"No DigitalOcean credentials found for instance '{instance_id}'. Cannot list droplets.")
        return []

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

def create_firewall(instance_config=None, instance_id="default"):
    """
    Create a DigitalOcean firewall for proxy droplets.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = settings.config["providers"]["digitalocean"]["instances"].get(instance_id, settings.config["providers"]["digitalocean"]["instances"]["default"])
    
    do_manager = get_manager(instance_id)

    if do_manager is None:
        logger.warning(f"No DigitalOcean credentials found for instance '{instance_id}'. Cannot create firewall.")
        return False

    fw = digitalocean.Firewall(
            token=do_manager.token, # Use token from the manager
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
    return True

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
