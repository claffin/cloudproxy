import itertools
import datetime

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers import settings
from cloudproxy.providers.hetzner.functions import list_proxies, delete_proxy, create_proxy
from cloudproxy.providers.settings import config, delete_queue, restart_queue
from cloudproxy.providers.rolling import rolling_manager


def hetzner_deployment(min_scaling, instance_config=None):
    """
    Deploy Hetzner servers based on min_scaling requirements.
    
    Args:
        min_scaling: The minimum number of servers to maintain
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"]["default"]
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")
    
    total_proxies = len(list_proxies(instance_config))
    if min_scaling < total_proxies:
        logger.info(f"Overprovisioned: Hetzner {display_name} destroying.....")
        for proxy in itertools.islice(
                list_proxies(instance_config), 0, (total_proxies - min_scaling)
        ):
            delete_proxy(proxy, instance_config)
            logger.info(f"Destroyed: Hetzner {display_name} -> {str(proxy.public_net.ipv4.ip)}")
            
    if min_scaling - total_proxies < 1:
        logger.info(f"Minimum Hetzner {display_name} proxies met")
    else:
        total_deploy = min_scaling - total_proxies
        logger.info(f"Deploying: {str(total_deploy)} Hetzner {display_name} proxy")
        for _ in range(total_deploy):
            create_proxy(instance_config)
            logger.info(f"Deployed Hetzner {display_name} proxy")
            
    return len(list_proxies(instance_config))


def hetzner_check_alive(instance_config=None):
    """
    Check if Hetzner servers are alive and operational.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"]["default"]
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")
    
    # Get instance name for rolling deployment tracking
    instance_name = next(
        (name for name, inst in config["providers"]["hetzner"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
    
    ip_ready = []
    pending_ips = []
    proxies_to_recycle = []
    
    for proxy in list_proxies(instance_config):
        elapsed = datetime.datetime.now(
            datetime.timezone.utc
        ) - dateparser.parse(str(proxy.created))
        if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
            # Queue for potential recycling
            proxies_to_recycle.append((proxy, elapsed))
        elif check_alive(proxy.public_net.ipv4.ip):
            logger.info(f"Alive: Hetzner {display_name} -> {str(proxy.public_net.ipv4.ip)}")
            ip_ready.append(proxy.public_net.ipv4.ip)
        else:
            if elapsed > datetime.timedelta(minutes=10):
                delete_proxy(proxy, instance_config)
                logger.info(
                    f"Destroyed: Hetzner {display_name} took too long -> {str(proxy.public_net.ipv4.ip)}"
                )
            else:
                logger.info(f"Waiting: Hetzner {display_name} -> {str(proxy.public_net.ipv4.ip)}")
                pending_ips.append(str(proxy.public_net.ipv4.ip))
    
    # Update rolling manager with current proxy health status
    rolling_manager.update_proxy_health("hetzner", instance_name, ip_ready, pending_ips)
    
    # Handle rolling deployments for age-limited proxies
    if proxies_to_recycle and config["rolling_deployment"]["enabled"]:
        rolling_config = config["rolling_deployment"]
        
        for prox, elapsed in proxies_to_recycle:
            proxy_ip = str(prox.public_net.ipv4.ip)
            
            # Check if we can recycle this proxy according to rolling deployment rules
            if rolling_manager.can_recycle_proxy(
                provider="hetzner",
                instance=instance_name,
                proxy_ip=proxy_ip,
                total_healthy=len(ip_ready),
                min_available=rolling_config["min_available"],
                batch_size=rolling_config["batch_size"],
                rolling_enabled=True,
                min_scaling=instance_config["scaling"]["min_scaling"]
            ):
                # Mark as recycling and delete
                rolling_manager.mark_proxy_recycling("hetzner", instance_name, proxy_ip)
                delete_proxy(prox, instance_config)
                rolling_manager.mark_proxy_recycled("hetzner", instance_name, proxy_ip)
                logger.info(f"Rolling deployment: Recycled Hetzner {display_name} proxy (age limit) -> {proxy_ip}")
            else:
                logger.info(f"Rolling deployment: Deferred recycling Hetzner {display_name} proxy -> {proxy_ip}")
    elif proxies_to_recycle and not config["rolling_deployment"]["enabled"]:
        # Standard non-rolling recycling
        for prox, elapsed in proxies_to_recycle:
            delete_proxy(prox, instance_config)
            logger.info(f"Recycling Hetzner {display_name} proxy, reached age limit -> {str(prox.public_net.ipv4.ip)}")
    
    return ip_ready


def hetzner_check_delete(instance_config=None):
    """
    Check if any Hetzner servers need to be deleted.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"]["default"]
        
    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")
    
    # Log current delete queue state
    if delete_queue:
        logger.info(f"Current delete queue contains {len(delete_queue)} IP addresses: {', '.join(delete_queue)}")
    
    servers = list_proxies(instance_config)
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
                delete_result = delete_proxy(server, instance_config)
                
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


def hetzner_start(instance_config=None):
    """
    Start the Hetzner provider lifecycle.
    
    Args:
        instance_config: The specific instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["hetzner"]["instances"]["default"]
        
    hetzner_check_delete(instance_config)
    hetzner_deployment(instance_config["scaling"]["min_scaling"], instance_config)
    ip_ready = hetzner_check_alive(instance_config)
    return ip_ready
