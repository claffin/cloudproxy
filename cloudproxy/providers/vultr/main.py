import datetime
import itertools

import dateparser
from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.vultr.functions import (
    create_proxy,
    list_instances,
    delete_proxy,
    create_firewall,
    VultrFirewallExistsException,
)
from cloudproxy.providers.settings import delete_queue, restart_queue, config
from cloudproxy.providers.rolling import rolling_manager


def vultr_deployment(min_scaling, instance_config=None):
    """
    Deploy Vultr instances based on min_scaling requirements.

    Args:
        min_scaling: The minimum number of instances to maintain
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["vultr"]["instances"]["default"]

    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")

    total_instances = len(list_instances(instance_config))
    if min_scaling < total_instances:
        logger.info(f"Overprovisioned: Vultr {display_name} destroying.....")
        for instance in itertools.islice(list_instances(
                instance_config), 0, (total_instances - min_scaling)):
            delete_proxy(instance, instance_config)
            logger.info(
                f"Destroyed: Vultr {display_name} -> {str(instance.ip_address)}")

    if min_scaling - total_instances < 1:
        logger.info(f"Minimum Vultr {display_name} instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info(
            f"Deploying: {str(total_deploy)} Vultr {display_name} instances")
        for _ in range(total_deploy):
            create_proxy(instance_config)
            logger.info(f"Deployed Vultr {display_name} instance")
    return len(list_instances(instance_config))


def vultr_check_alive(instance_config=None):
    """
    Check if Vultr instances are alive and operational.

    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["vultr"]["instances"]["default"]

    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")
    
    # Get instance name for rolling deployment tracking
    instance_name = next(
        (name for name, inst in config["providers"]["vultr"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )

    ip_ready = []
    pending_ips = []
    instances_to_recycle = []
    
    for instance in list_instances(instance_config):
        try:
            # Parse the created_at timestamp to a datetime object
            created_at = dateparser.parse(instance.date_created)
            if created_at is None:
                # If parsing fails but doesn't raise an exception, log and
                # continue
                logger.info(
                    f"Pending: Vultr {display_name} allocating (invalid timestamp)")
                continue

            # Calculate elapsed time
            elapsed = datetime.datetime.now(datetime.timezone.utc) - created_at

            # Check if the instance has reached the age limit
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(
                    seconds=config["age_limit"]):
                # Queue for potential recycling
                instances_to_recycle.append((instance, elapsed))
            elif instance.status == "active" and instance.ip_address and check_alive(instance.ip_address):
                logger.info(
                    f"Alive: Vultr {display_name} -> {str(instance.ip_address)}")
                ip_ready.append(instance.ip_address)
            else:
                # Check if the instance has been pending for too long
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(instance, instance_config)
                    logger.info(
                        f"Destroyed: took too long Vultr {display_name} -> {str(instance.ip_address)}"
                    )
                else:
                    logger.info(
                        f"Waiting: Vultr {display_name} -> {str(instance.ip_address)}")
                    if instance.ip_address:
                        pending_ips.append(instance.ip_address)
        except TypeError:
            # This happens when dateparser.parse raises a TypeError
            logger.info(f"Pending: Vultr {display_name} allocating")
            if hasattr(instance, 'ip_address') and instance.ip_address:
                pending_ips.append(instance.ip_address)
    
    # Update rolling manager with current proxy health status
    rolling_manager.update_proxy_health("vultr", instance_name, ip_ready, pending_ips)
    
    # Handle rolling deployments for age-limited instances
    if instances_to_recycle and config["rolling_deployment"]["enabled"]:
        rolling_config = config["rolling_deployment"]
        
        for inst, elapsed in instances_to_recycle:
            if inst.ip_address:
                instance_ip = str(inst.ip_address)
                
                # Check if we can recycle this instance according to rolling deployment rules
                if rolling_manager.can_recycle_proxy(
                    provider="vultr",
                    instance=instance_name,
                    proxy_ip=instance_ip,
                    total_healthy=len(ip_ready),
                    min_available=rolling_config["min_available"],
                    batch_size=rolling_config["batch_size"],
                    rolling_enabled=True,
                    min_scaling=instance_config["scaling"]["min_scaling"]
                ):
                    # Mark as recycling and delete
                    rolling_manager.mark_proxy_recycling("vultr", instance_name, instance_ip)
                    delete_proxy(inst, instance_config)
                    rolling_manager.mark_proxy_recycled("vultr", instance_name, instance_ip)
                    logger.info(
                        f"Rolling deployment: Recycled Vultr {display_name} instance (age limit) -> {instance_ip}"
                    )
                else:
                    logger.info(
                        f"Rolling deployment: Deferred recycling Vultr {display_name} instance -> {instance_ip}"
                    )
    elif instances_to_recycle and not config["rolling_deployment"]["enabled"]:
        # Standard non-rolling recycling
        for inst, elapsed in instances_to_recycle:
            delete_proxy(inst, instance_config)
            logger.info(
                f"Recycling Vultr {display_name} instance, reached age limit -> {str(inst.ip_address)}"
            )
    
    return ip_ready


def vultr_check_delete(instance_config=None):
    """
    Check if any Vultr instances need to be deleted.

    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["vultr"]["instances"]["default"]

    # Get instance display name for logging
    display_name = instance_config.get("display_name", "default")

    # Log current delete queue state
    if delete_queue:
        logger.info(
            f"Current delete queue contains {len(delete_queue)} IP addresses: {', '.join(delete_queue)}")

    instances = list_instances(instance_config)
    if not instances:
        logger.info(
            f"No Vultr {display_name} instances found to process for deletion")
        return

    logger.info(
        f"Checking {len(instances)} Vultr {display_name} instances for deletion")

    for instance in instances:
        try:
            instance_ip = str(instance.ip_address)

            # Check if this instance's IP is in the delete or restart queue
            if instance_ip in delete_queue or instance_ip in restart_queue:
                logger.info(
                    f"Found instance {instance.id} with IP {instance_ip} in deletion queue - deleting now")

                # Attempt to delete the instance
                delete_result = delete_proxy(instance, instance_config)

                if delete_result:
                    logger.info(
                        f"Successfully destroyed Vultr {display_name} instance -> {instance_ip}")

                    # Remove from queues upon successful deletion
                    if instance_ip in delete_queue:
                        delete_queue.remove(instance_ip)
                        logger.info(f"Removed {instance_ip} from delete queue")
                    if instance_ip in restart_queue:
                        restart_queue.remove(instance_ip)
                        logger.info(
                            f"Removed {instance_ip} from restart queue")
                else:
                    logger.warning(
                        f"Failed to destroy Vultr {display_name} instance -> {instance_ip}")
        except Exception as e:
            logger.error(f"Error processing instance for deletion: {e}")
            continue

    # Report on any IPs that remain in the queues but weren't found
    remaining_delete = [
        ip for ip in delete_queue if any(
            ip == str(
                i.ip_address) for i in instances)]
    if remaining_delete:
        logger.warning(
            f"IPs remaining in delete queue that weren't found as instances: {', '.join(remaining_delete)}")


def vultr_fw(instance_config=None):
    """
    Create a Vultr firewall for proxy instances.

    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["vultr"]["instances"]["default"]

    # Get instance name for logging
    instance_id = next(
        (name for name, inst in config["providers"]["vultr"]["instances"].items()
         if inst == instance_config),
        "default"
    )

    try:
        firewall_id = create_firewall(instance_config)
        if firewall_id:
            logger.info(
                f"Created firewall 'cloudproxy-{instance_id}' with ID: {firewall_id}")
    except VultrFirewallExistsException as e:
        logger.debug(str(e))
    except Exception as e:
        logger.error(f"Error creating firewall: {e}")


def vultr_start(instance_config=None):
    """
    Start the Vultr provider lifecycle.

    Args:
        instance_config: The specific instance configuration

    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["vultr"]["instances"]["default"]

    vultr_fw(instance_config)
    vultr_check_delete(instance_config)
    # First check which instances are alive
    vultr_check_alive(instance_config)
    # Then handle deployment/scaling based on ready instances
    vultr_deployment(
        instance_config["scaling"]["min_scaling"],
        instance_config)
    # Final check for alive instances
    return vultr_check_alive(instance_config)
