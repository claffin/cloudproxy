import datetime
import itertools

from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.aws.functions import (
    list_instances,
    create_proxy,
    delete_proxy,
    stop_proxy,
    start_proxy,
)
from cloudproxy.providers.settings import delete_queue, restart_queue, config
from cloudproxy.providers.rolling import rolling_manager


def aws_deployment(min_scaling, instance_config=None):
    """
    Deploy AWS instances based on min_scaling requirements.
    
    Args:
        min_scaling: The minimum number of instances to maintain
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"]["default"]
        
    total_instances = len(list_instances(instance_config))
    if min_scaling < total_instances:
        logger.info(f"Overprovisioned: AWS {instance_config.get('display_name', 'default')} destroying.....")
        for instance in itertools.islice(
            list_instances(instance_config), 0, (total_instances - min_scaling)
        ):
            delete_proxy(instance["Instances"][0]["InstanceId"], instance_config)
            try:
                msg = instance["Instances"][0]["PublicIpAddress"]
            except KeyError:
                msg = instance["Instances"][0]["InstanceId"]

            logger.info(f"Destroyed: AWS {instance_config.get('display_name', 'default')} -> " + msg)
    if min_scaling - total_instances < 1:
        logger.info(f"Minimum AWS {instance_config.get('display_name', 'default')} instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info(f"Deploying: {str(total_deploy)} AWS {instance_config.get('display_name', 'default')} instances")
        for _ in range(total_deploy):
            create_proxy(instance_config)
            logger.info(f"Deployed AWS {instance_config.get('display_name', 'default')} instance")
    return len(list_instances(instance_config))


def aws_check_alive(instance_config=None):
    """
    Check if AWS instances are alive and operational.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"]["default"]
    
    # Get instance name for rolling deployment tracking
    instance_name = next(
        (name for name, inst in config["providers"]["aws"]["instances"].items() 
         if inst == instance_config), 
        "default"
    )
        
    ip_ready = []
    pending_ips = []
    instances_to_recycle = []
    
    # First pass: identify healthy and pending instances
    for instance in list_instances(instance_config):
        try:
            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - instance["Instances"][0]["LaunchTime"]
            
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                # Queue for potential recycling
                instances_to_recycle.append((instance, elapsed))
            elif instance["Instances"][0]["State"]["Name"] == "stopped":
                logger.info(
                    f"Waking up: AWS {instance_config.get('display_name', 'default')} -> Instance " + instance["Instances"][0]["InstanceId"]
                )
                started = start_proxy(instance["Instances"][0]["InstanceId"], instance_config)
                if not started:
                    logger.info(
                        "Could not wake up due to IncorrectSpotRequestState, trying again later."
                    )
            elif instance["Instances"][0]["State"]["Name"] == "stopping":
                logger.info(
                    f"Stopping: AWS {instance_config.get('display_name', 'default')} -> " + instance["Instances"][0]["PublicIpAddress"]
                )
            elif instance["Instances"][0]["State"]["Name"] == "pending":
                logger.info(
                    f"Pending: AWS {instance_config.get('display_name', 'default')} -> " + instance["Instances"][0]["PublicIpAddress"]
                )
                if "PublicIpAddress" in instance["Instances"][0]:
                    pending_ips.append(instance["Instances"][0]["PublicIpAddress"])
            # Must be "running" if none of the above, check if alive or not.
            elif check_alive(instance["Instances"][0]["PublicIpAddress"]):
                logger.info(
                    f"Alive: AWS {instance_config.get('display_name', 'default')} -> " + instance["Instances"][0]["PublicIpAddress"]
                )
                ip_ready.append(instance["Instances"][0]["PublicIpAddress"])
            else:
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(instance["Instances"][0]["InstanceId"], instance_config)
                    logger.info(
                        f"Destroyed: took too long AWS {instance_config.get('display_name', 'default')} -> "
                        + instance["Instances"][0]["PublicIpAddress"]
                    )
                else:
                    logger.info(
                        f"Waiting: AWS {instance_config.get('display_name', 'default')} -> " + instance["Instances"][0]["PublicIpAddress"]
                    )
                    if "PublicIpAddress" in instance["Instances"][0]:
                        pending_ips.append(instance["Instances"][0]["PublicIpAddress"])
        except (TypeError, KeyError):
            logger.info(f"Pending: AWS {instance_config.get('display_name', 'default')} -> allocating ip")
    
    # Update rolling manager with current proxy health status
    rolling_manager.update_proxy_health("aws", instance_name, ip_ready, pending_ips)
    
    # Handle rolling deployments for age-limited instances
    if instances_to_recycle and config["rolling_deployment"]["enabled"]:
        rolling_config = config["rolling_deployment"]
        
        for inst, elapsed in instances_to_recycle:
            if "PublicIpAddress" in inst["Instances"][0]:
                instance_ip = inst["Instances"][0]["PublicIpAddress"]
                
                # Check if we can recycle this instance according to rolling deployment rules
                if rolling_manager.can_recycle_proxy(
                    provider="aws",
                    instance=instance_name,
                    proxy_ip=instance_ip,
                    total_healthy=len(ip_ready),
                    min_available=rolling_config["min_available"],
                    batch_size=rolling_config["batch_size"],
                    rolling_enabled=True,
                    min_scaling=instance_config["scaling"]["min_scaling"]
                ):
                    # Mark as recycling and delete
                    rolling_manager.mark_proxy_recycling("aws", instance_name, instance_ip)
                    delete_proxy(inst["Instances"][0]["InstanceId"], instance_config)
                    rolling_manager.mark_proxy_recycled("aws", instance_name, instance_ip)
                    logger.info(
                        f"Rolling deployment: Recycled AWS {instance_config.get('display_name', 'default')} instance (age limit) -> {instance_ip}"
                    )
                else:
                    logger.info(
                        f"Rolling deployment: Deferred recycling AWS {instance_config.get('display_name', 'default')} instance -> {instance_ip}"
                    )
    elif instances_to_recycle and not config["rolling_deployment"]["enabled"]:
        # Standard non-rolling recycling
        for inst, elapsed in instances_to_recycle:
            delete_proxy(inst["Instances"][0]["InstanceId"], instance_config)
            if "PublicIpAddress" in inst["Instances"][0]:
                logger.info(
                    f"Recycling AWS {instance_config.get('display_name', 'default')} instance, reached age limit -> " + inst["Instances"][0]["PublicIpAddress"]
                )
            else:
                logger.info(
                    f"Recycling AWS {instance_config.get('display_name', 'default')} instance, reached age limit -> " + inst["Instances"][0]["InstanceId"]
                )
    
    return ip_ready


def aws_check_delete(instance_config=None):
    """
    Check if any AWS instances need to be deleted.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"]["default"]
        
    for instance in list_instances(instance_config):
        if instance["Instances"][0].get("PublicIpAddress") in delete_queue:
            delete_proxy(instance["Instances"][0]["InstanceId"], instance_config)
            logger.info(
                f"Destroyed: not wanted AWS {instance_config.get('display_name', 'default')} -> "
                + instance["Instances"][0]["PublicIpAddress"]
            )
            delete_queue.remove(instance["Instances"][0]["PublicIpAddress"])


def aws_check_stop(instance_config=None):
    """
    Check if any AWS instances need to be stopped.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"]["default"]
        
    for instance in list_instances(instance_config):
        if instance["Instances"][0].get("PublicIpAddress") in restart_queue:
            stop_proxy(instance["Instances"][0]["InstanceId"], instance_config)
            logger.info(
                f"Stopped: getting new IP AWS {instance_config.get('display_name', 'default')} -> "
                + instance["Instances"][0]["PublicIpAddress"]
            )
            restart_queue.remove(instance["Instances"][0]["PublicIpAddress"])


def aws_start(instance_config=None):
    """
    Start the AWS provider lifecycle.
    
    Args:
        instance_config: The specific instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"]["default"]
        
    aws_check_delete(instance_config)
    aws_check_stop(instance_config)
    aws_deployment(instance_config["scaling"]["min_scaling"], instance_config)
    ip_ready = aws_check_alive(instance_config)
    return ip_ready
