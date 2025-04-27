import datetime
import itertools

from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.scaleway.functions import (
    list_instances,
    create_proxy,
    delete_proxy,
    stop_proxy,
    start_proxy,
)
from cloudproxy.providers.settings import delete_queue, restart_queue, config


def scaleway_deployment(min_scaling, instance_config=None):
    """
    Deploy Scaleway instances based on min_scaling requirements.
    
    Args:
        min_scaling: The minimum number of instances to maintain
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
        
    total_instances = len(list_instances(instance_config))
    if min_scaling < total_instances:
        logger.info(f"Overprovisioned: Scaleway {instance_config.get('display_name', 'default')} destroying.....")
        for instance in itertools.islice(
            list_instances(instance_config), 0, (total_instances - min_scaling)
        ):
            delete_proxy(instance["id"], instance_config)
            try:
                msg = instance["public_ip"]["address"]
            except KeyError:
                msg = instance["id"]

            logger.info(f"Destroyed: Scaleway {instance_config.get('display_name', 'default')} -> " + msg)
    if min_scaling - total_instances < 1:
        logger.info(f"Minimum Scaleway {instance_config.get('display_name', 'default')} instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info(f"Deploying: {str(total_deploy)} Scaleway {instance_config.get('display_name', 'default')} instances")
        for _ in range(total_deploy):
            create_proxy(instance_config)
            logger.info(f"Deployed Scaleway {instance_config.get('display_name', 'default')} instance")
    return len(list_instances(instance_config))


def scaleway_check_alive(instance_config=None):
    """
    Check if Scaleway instances are alive and operational.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
        
    ip_ready = []
    for instance in list_instances(instance_config):
        try:
            # Scaleway API doesn't provide creation time directly, we'll use a workaround
            if "creation_date" in instance:
                creation_time = datetime.datetime.fromisoformat(instance["creation_date"].replace('Z', '+00:00'))
                elapsed = datetime.datetime.now(datetime.timezone.utc) - creation_time
                
                if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                    delete_proxy(instance["id"], instance_config)
                    logger.info(
                        f"Recycling Scaleway {instance_config.get('display_name', 'default')} instance, reached age limit -> " + instance["public_ip"]["address"]
                    )
            
            if instance["state"] == "stopped":
                logger.info(
                    f"Waking up: Scaleway {instance_config.get('display_name', 'default')} -> Instance " + instance["id"]
                )
                start_proxy(instance["id"], instance_config)
            elif instance["state"] == "stopping":
                logger.info(
                    f"Stopping: Scaleway {instance_config.get('display_name', 'default')} -> " + instance["public_ip"]["address"]
                )
            elif instance["state"] == "starting":
                logger.info(
                    f"Starting: Scaleway {instance_config.get('display_name', 'default')} -> " + instance["public_ip"]["address"]
                )
            # Must be "running" if not any of the above, check if alive
            elif instance["state"] == "running" and check_alive(instance["public_ip"]["address"]):
                logger.info(
                    f"Alive: Scaleway {instance_config.get('display_name', 'default')} -> " + instance["public_ip"]["address"]
                )
                ip_ready.append(instance["public_ip"]["address"])
            else:
                # Check if instance is taking too long to start
                if "creation_date" in instance:
                    creation_time = datetime.datetime.fromisoformat(instance["creation_date"].replace('Z', '+00:00'))
                    elapsed = datetime.datetime.now(datetime.timezone.utc) - creation_time
                    if elapsed > datetime.timedelta(minutes=10):
                        delete_proxy(instance["id"], instance_config)
                        logger.info(
                            f"Destroyed: took too long Scaleway {instance_config.get('display_name', 'default')} -> "
                            + instance["public_ip"]["address"]
                        )
                    else:
                        logger.info(
                            f"Waiting: Scaleway {instance_config.get('display_name', 'default')} -> " + instance["public_ip"]["address"]
                        )
        except (TypeError, KeyError):
            logger.info(f"Pending: Scaleway {instance_config.get('display_name', 'default')} -> allocating ip")
    return ip_ready


def scaleway_check_delete(instance_config=None):
    """
    Check if any Scaleway instances need to be deleted.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
        
    for instance in list_instances(instance_config):
        if "public_ip" in instance and instance["public_ip"]["address"] in delete_queue:
            delete_proxy(instance["id"], instance_config)
            logger.info(
                f"Destroyed: not wanted Scaleway {instance_config.get('display_name', 'default')} -> "
                + instance["public_ip"]["address"]
            )
            delete_queue.remove(instance["public_ip"]["address"])


def scaleway_check_stop(instance_config=None):
    """
    Check if any Scaleway instances need to be stopped.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
        
    for instance in list_instances(instance_config):
        if "public_ip" in instance and instance["public_ip"]["address"] in restart_queue:
            stop_proxy(instance["id"], instance_config)
            logger.info(
                f"Stopped: getting new IP Scaleway {instance_config.get('display_name', 'default')} -> "
                + instance["public_ip"]["address"]
            )
            restart_queue.remove(instance["public_ip"]["address"])


def scaleway_start(instance_config=None):
    """
    Start the Scaleway provider lifecycle.
    
    Args:
        instance_config: The specific instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["scaleway"]["instances"]["default"]
        
    scaleway_check_delete(instance_config)
    scaleway_check_stop(instance_config)
    scaleway_deployment(instance_config["scaling"]["min_scaling"], instance_config)
    ip_ready = scaleway_check_alive(instance_config)
    return ip_ready 