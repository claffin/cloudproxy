import itertools
import datetime

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers import settings
from cloudproxy.providers.hetzner.functions import list_proxies, delete_proxy, create_proxy
from cloudproxy.providers.settings import config, delete_queue, restart_queue


def hetzner_deployment(min_scaling, instance_config=None, instance_id="default"):
    """
    Deploy Hetzner servers based on min_scaling requirements for a specific instance.
    
    Args:
        min_scaling: The minimum number of servers to maintain
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"].get(instance_id, config["providers"]["hetzner"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for Hetzner instance '{instance_id}'. Skipping deployment.")
        return 0
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", instance_id)
    
    total_proxies = len(list_proxies(instance_id=instance_id))
    if min_scaling < total_proxies:
        logger.info(f"Overprovisioned: Hetzner {display_name} destroying.....")
        for proxy in itertools.islice(
                list_proxies(instance_id=instance_id), 0, (total_proxies - min_scaling)
        ):
            delete_proxy(proxy, instance_id=instance_id)
            logger.info(f"Destroyed: Hetzner {display_name} -> {str(proxy.public_net.ipv4.ip)}")
            
    if min_scaling - total_proxies < 1:
        logger.info(f"Minimum Hetzner {display_name} proxies met")
    else:
        total_deploy = min_scaling - total_proxies
        logger.info(f"Deploying: {str(total_deploy)} Hetzner {display_name} proxy")
        for _ in range(total_deploy):
            create_proxy(instance_config, instance_id=instance_id)
            logger.info(f"Deployed Hetzner {display_name} proxy")
            
    return len(list_proxies(instance_id=instance_id))


def hetzner_check_alive(instance_config=None, instance_id="default"):
    """
    Check if Hetzner servers are alive and operational for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"].get(instance_id, config["providers"]["hetzner"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for Hetzner instance '{instance_id}'. Skipping check alive.")
        return []
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", instance_id)
    
    ip_ready = []
    for proxy in list_proxies(instance_id=instance_id):
        try:
            created_at = dateparser.parse(str(proxy.created))
            if created_at is None:
                logger.info(f"Pending: Hetzner {display_name} allocating (invalid timestamp)")
                continue

            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - created_at

            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                delete_proxy(proxy, instance_id=instance_id)
                logger.info(
                    f"Recycling Hetzner {display_name} proxy, reached age limit -> {str(proxy.public_net.ipv4.ip)}"
                )
            elif check_alive(proxy.public_net.ipv4.ip):
                logger.info(f"Alive: Hetzner {display_name} -> {str(proxy.public_net.ipv4.ip)}")
                ip_ready.append(proxy.public_net.ipv4.ip)
            else:
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(proxy, instance_id=instance_id)
                    logger.info(
                        f"Destroyed: Hetzner {display_name} took too long -> {str(proxy.public_net.ipv4.ip)}"
                    )
                else:
                    logger.info(f"Waiting: Hetzner {display_name} -> {str(proxy.public_net.ipv4.ip)}")
        except Exception as e:
             logger.info(f"Pending: Hetzner {display_name} allocating (Error: {e})")
    return ip_ready


def hetzner_check_delete(instance_config=None, instance_id="default"):
    """
    Check if any Hetzner servers need to be deleted for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"].get(instance_id, config["providers"]["hetzner"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for Hetzner instance '{instance_id}'. Skipping check delete.")
        return
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", instance_id)
    
    # Log current delete queue state
    if delete_queue:
        logger.info(f"Current delete queue contains {len(delete_queue)} IP addresses: {', '.join(delete_queue)}")
    
    servers = list_proxies(instance_id=instance_id)
    if not servers:
        logger.info(f"No Hetzner {display_name} servers found to process for deletion")
        return
        
    logger.info(f"Checking {len(servers)} Hetzner {display_name} servers for deletion")
    
    for server in servers:
        try:
            server_ip = str(server.public_net.ipv4.ip)
            
            # Check if this server's IP is in the delete or restart queue
            if server_ip in delete_queue or server_ip in restart_queue:
                logger.info(f"Found server {server.id} with IP {server_ip} in deletion queue - deleting now")
                
                # Attempt to delete the server
                delete_result = delete_proxy(server, instance_id=instance_id)
                
                if delete_result:
                    logger.info(f"Successfully destroyed Hetzner {display_name} server -> {server_ip}")
                    
                    # Remove from queues upon successful deletion
                    if server_ip in delete_queue:
                        delete_queue.remove(server_ip)
                        logger.info(f"Removed {server_ip} from delete queue")
                    if server_ip in restart_queue:
                        restart_queue.remove(server_ip)
                        logger.info(f"Removed {server_ip} from restart queue")
                else:
                    logger.warning(f"Failed to destroy Hetzner {display_name} server -> {server_ip}")
        except Exception as e:
            logger.error(f"Error processing server for deletion: {e}")
            continue
    
    # Report on any IPs that remain in the queues but weren't found
    remaining_delete = [ip for ip in delete_queue if any(ip == str(s.public_net.ipv4.ip) for s in servers)]
    if remaining_delete:
        logger.warning(f"IPs remaining in delete queue that weren't found as servers: {', '.join(remaining_delete)}")


def hetzner_start(instance_config=None, instance_id="default"):
    """
    Start the Hetzner provider lifecycle for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"].get(instance_id, config["providers"]["hetzner"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for Hetzner instance '{instance_id}'. Skipping startup.")
        return []
        
    hetzner_check_delete(instance_config, instance_id=instance_id)
    hetzner_deployment(instance_config["scaling"]["min_scaling"], instance_config, instance_id=instance_id)
    ip_ready = hetzner_check_alive(instance_config, instance_id=instance_id)
    return ip_ready
