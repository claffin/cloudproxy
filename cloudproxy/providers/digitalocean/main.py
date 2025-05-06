import datetime
import itertools

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.digitalocean.functions import (
    create_proxy,
    list_droplets,
    delete_proxy,
    create_firewall,
    DOFirewallExistsException,
)
from cloudproxy.providers import settings
from cloudproxy.providers.settings import delete_queue, restart_queue, config


def do_deployment(min_scaling, instance_config=None, instance_id="default"):
    """
    Deploy DigitalOcean droplets based on min_scaling requirements.
    
    Args:
        min_scaling: The minimum number of droplets to maintain
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"].get(instance_id, config["providers"]["digitalocean"]["instances"]["default"])
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", instance_id)
    
    total_droplets = len(list_droplets(instance_id=instance_id))
    if min_scaling < total_droplets:
        logger.info(f"Overprovisioned: DO {display_name} destroying.....")
        for droplet in itertools.islice(list_droplets(instance_id=instance_id), 0, (total_droplets - min_scaling)):
            delete_proxy(droplet, instance_id=instance_id)
            logger.info(f"Destroyed: DO {display_name} -> {str(droplet.ip_address)}")
            
    if min_scaling - total_droplets < 1:
        logger.info(f"Minimum DO {display_name} Droplets met")
    else:
        total_deploy = min_scaling - total_droplets
        logger.info(f"Deploying: {str(total_deploy)} DO {display_name} droplets")
        for _ in range(total_deploy):
            create_proxy(instance_config, instance_id=instance_id)
            logger.info(f"Deployed DO {display_name} droplet")
    return len(list_droplets(instance_id=instance_id))


def do_check_alive(instance_config=None, instance_id="default"):
    """
    Check if DigitalOcean droplets are alive and operational.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"].get(instance_id, config["providers"]["digitalocean"]["instances"]["default"])
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", instance_id)
    
    ip_ready = []
    for droplet in list_droplets(instance_id=instance_id):
        try:
            # Parse the created_at timestamp to a datetime object
            created_at = dateparser.parse(droplet.created_at)
            if created_at is None:
                # If parsing fails but doesn't raise an exception, log and continue
                logger.info(f"Pending: DO {display_name} allocating (invalid timestamp)")
                continue
                
            # Calculate elapsed time
            elapsed = datetime.datetime.now(datetime.timezone.utc) - created_at
            
            # Check if the droplet has reached the age limit
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                delete_proxy(droplet, instance_id=instance_id)
                logger.info(
                    f"Recycling DO {display_name} droplet, reached age limit -> {str(droplet.ip_address)}"
                )
            elif check_alive(droplet.ip_address):
                logger.info(f"Alive: DO {display_name} -> {str(droplet.ip_address)}")
                ip_ready.append(droplet.ip_address)
            else:
                # Check if the droplet has been pending for too long
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(droplet, instance_id=instance_id)
                    logger.info(
                        f"Destroyed: took too long DO {display_name} -> {str(droplet.ip_address)}"
                    )
                else:
                    logger.info(f"Waiting: DO {display_name} -> {str(droplet.ip_address)}")
        except TypeError:
            # This happens when dateparser.parse raises a TypeError
            logger.info(f"Pending: DO {display_name} allocating")
    return ip_ready


def do_check_delete(instance_config=None, instance_id="default"):
    """
    Check if any DigitalOcean droplets need to be deleted.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"].get(instance_id, config["providers"]["digitalocean"]["instances"]["default"])
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", instance_id)
    
    # Log current delete queue state
    if delete_queue:
        logger.info(f"Current delete queue contains {len(delete_queue)} IP addresses: {', '.join(delete_queue)}")
    
    droplets = list_droplets(instance_id=instance_id)
    if not droplets:
        logger.info(f"No DigitalOcean {display_name} droplets found to process for deletion")
        return
        
    logger.info(f"Checking {len(droplets)} DigitalOcean {display_name} droplets for deletion")
    
    for droplet in droplets:
        try:
            droplet_ip = str(droplet.ip_address)
            
            # Check if this droplet's IP is in the delete or restart queue
            if droplet_ip in delete_queue or droplet_ip in restart_queue:
                logger.info(f"Found droplet {droplet.id} with IP {droplet_ip} in deletion queue - deleting now")
                
                # Attempt to delete the droplet
                delete_result = delete_proxy(droplet, instance_id=instance_id)
                
                if delete_result:
                    logger.info(f"Successfully destroyed DigitalOcean {display_name} droplet -> {droplet_ip}")
                    
                    # Remove from queues upon successful deletion
                    if droplet_ip in delete_queue:
                        delete_queue.remove(droplet_ip)
                        logger.info(f"Removed {droplet_ip} from delete queue")
                    if droplet_ip in restart_queue:
                        restart_queue.remove(droplet_ip)
                        logger.info(f"Removed {droplet_ip} from restart queue")
                else:
                    logger.warning(f"Failed to destroy DigitalOcean {display_name} droplet -> {droplet_ip}")
        except Exception as e:
            logger.error(f"Error processing droplet for deletion: {e}")
            continue
    
    # Report on any IPs that remain in the queues but weren't found
    remaining_delete = [ip for ip in delete_queue if any(ip == str(d.ip_address) for d in droplets)]
    if remaining_delete:
        logger.warning(f"IPs remaining in delete queue that weren't found as droplets: {', '.join(remaining_delete)}")

def do_fw(instance_config=None, instance_id="default"):
    """
    Create a DigitalOcean firewall for proxy droplets.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"].get(instance_id, config["providers"]["digitalocean"]["instances"]["default"])
        
    # Get instance name for logging
    display_name = instance_config.get("display_name", instance_id)
    
    try:
        create_firewall(instance_config, instance_id=instance_id)
        logger.info(f"Created firewall 'cloudproxy-{instance_id}' for instance '{display_name}'")
    except DOFirewallExistsException as e:
        logger.info(f"Firewall 'cloudproxy-{instance_id}' already exists for instance '{display_name}'.")
        pass
    except Exception as e:
        logger.error(f"Error creating firewall for instance '{display_name}': {e}")


def do_start(instance_config=None, instance_id="default"):
    """
    Start the DigitalOcean provider lifecycle for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"].get(instance_id, config["providers"]["digitalocean"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for DigitalOcean instance '{instance_id}'. Skipping startup.")
        return []
        
    do_fw(instance_config, instance_id=instance_id)
    do_check_delete(instance_config, instance_id=instance_id)
    # First check which droplets are alive
    ip_ready = do_check_alive(instance_config, instance_id=instance_id)
    # Then handle deployment/scaling based on ready droplets
    do_deployment(instance_config["scaling"]["min_scaling"], instance_config, instance_id=instance_id)
    # Final check for alive droplets
    return do_check_alive(instance_config, instance_id=instance_id)
