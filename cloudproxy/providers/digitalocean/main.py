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


def do_deployment(min_scaling, instance_config=None):
    """
    Deploy DigitalOcean droplets based on min_scaling requirements.
    
    Args:
        min_scaling: The minimum number of droplets to maintain
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"]["default"]
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")
    
    total_droplets = len(list_droplets(instance_config))
    if min_scaling < total_droplets:
        logger.info(f"Overprovisioned: DO {display_name} destroying.....")
        for droplet in itertools.islice(list_droplets(instance_config), 0, (total_droplets - min_scaling)):
            delete_proxy(droplet, instance_config)
            logger.info(f"Destroyed: DO {display_name} -> {str(droplet.ip_address)}")
            
    if min_scaling - total_droplets < 1:
        logger.info(f"Minimum DO {display_name} Droplets met")
    else:
        total_deploy = min_scaling - total_droplets
        logger.info(f"Deploying: {str(total_deploy)} DO {display_name} droplets")
        for _ in range(total_deploy):
            create_proxy(instance_config)
            logger.info(f"Deployed DO {display_name} droplet")
    return len(list_droplets(instance_config))


def do_check_alive(instance_config=None):
    """
    Check if DigitalOcean droplets are alive and operational.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"]["default"]
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")
    
    ip_ready = []
    for droplet in list_droplets(instance_config):
        try:
            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - dateparser.parse(droplet.created_at)
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                delete_proxy(droplet, instance_config)
                logger.info(
                    f"Recycling DO {display_name} droplet, reached age limit -> {str(droplet.ip_address)}"
                )
            elif check_alive(droplet.ip_address):
                logger.info(f"Alive: DO {display_name} -> {str(droplet.ip_address)}")
                ip_ready.append(droplet.ip_address)
            else:
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(droplet, instance_config)
                    logger.info(
                        f"Destroyed: took too long DO {display_name} -> {str(droplet.ip_address)}"
                    )
                else:
                    logger.info(f"Waiting: DO {display_name} -> {str(droplet.ip_address)}")
        except TypeError:
            logger.info(f"Pending: DO {display_name} allocating")
    return ip_ready


def do_check_delete(instance_config=None):
    """
    Check if any DigitalOcean droplets need to be deleted.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"]["default"]
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")
    
    for droplet in list_droplets(instance_config):
        if droplet.ip_address in delete_queue or droplet.ip_address in restart_queue:
            delete_proxy(droplet, instance_config)
            logger.info(f"Destroyed: not wanted DO {display_name} -> {str(droplet.ip_address)}")
            if droplet.ip_address in delete_queue:
                delete_queue.remove(droplet.ip_address)
            if droplet.ip_address in restart_queue:
                restart_queue.remove(droplet.ip_address)

def do_fw(instance_config=None):
    """
    Create a DigitalOcean firewall for proxy droplets.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"]["default"]
        
    # Get instance name for logging
    instance_id = next(
        (name for name, inst in config["providers"]["digitalocean"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    try:
        create_firewall(instance_config)
        logger.info(f"Created firewall 'cloudproxy-{instance_id}'")
    except DOFirewallExistsException as e:
        pass
    except Exception as e:
        logger.error(e)

def do_start(instance_config=None):
    """
    Start the DigitalOcean provider lifecycle.
    
    Args:
        instance_config: The specific instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["digitalocean"]["instances"]["default"]
        
    do_fw(instance_config)
    do_check_delete(instance_config)
    # First check which droplets are alive
    ip_ready = do_check_alive(instance_config)
    # Then handle deployment/scaling based on ready droplets
    do_deployment(instance_config["scaling"]["min_scaling"], instance_config)
    # Final check for alive droplets
    return do_check_alive(instance_config)
