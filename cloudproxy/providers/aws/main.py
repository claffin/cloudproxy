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


def aws_deployment(min_scaling, instance_config=None, instance_id="default"):
    """
    Deploy AWS instances based on min_scaling requirements.
    
    Args:
        min_scaling: The minimum number of instances to maintain
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(instance_id, config["providers"]["aws"]["instances"]["default"])
        
    total_instances = len(list_instances(instance_id=instance_id))
    if min_scaling < total_instances:
        logger.info(f"Overprovisioned: AWS {instance_config.get('display_name', instance_id)} destroying.....")
        for instance in itertools.islice(
            list_instances(instance_id=instance_id), 0, (total_instances - min_scaling)
        ):
            delete_proxy(instance["Instances"][0]["InstanceId"], config_instance_id=instance_id)
            try:
                msg = instance["Instances"][0]["PublicIpAddress"]
            except KeyError:
                msg = instance["Instances"][0]["InstanceId"]

            logger.info(f"Destroyed: AWS {instance_config.get('display_name', instance_id)} -> " + msg)
    if min_scaling - total_instances < 1:
        logger.info(f"Minimum AWS {instance_config.get('display_name', instance_id)} instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info(f"Deploying: {str(total_deploy)} AWS {instance_config.get('display_name', instance_id)} instances")
        for _ in range(total_deploy):
            create_proxy(instance_config, instance_id=instance_id)
            logger.info(f"Deployed AWS {instance_config.get('display_name', instance_id)} instance")
    return len(list_instances(instance_id=instance_id))


def aws_check_alive(instance_config=None, instance_id="default"):
    """
    Check if AWS instances are alive and operational.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(instance_id, config["providers"]["aws"]["instances"]["default"])
        
    ip_ready = []
    for instance in list_instances(instance_id=instance_id):
        try:
            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - instance["Instances"][0]["LaunchTime"]
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                delete_proxy(instance["Instances"][0]["InstanceId"], config_instance_id=instance_id)
                logger.info(
                    f"Recycling AWS {instance_config.get('display_name', instance_id)} instance, reached age limit -> " + instance["Instances"][0]["PublicIpAddress"]
                )
            elif instance["Instances"][0]["State"]["Name"] == "stopped":
                logger.info(
                    f"Waking up: AWS {instance_config.get('display_name', instance_id)} -> Instance " + instance["Instances"][0]["InstanceId"]
                )
                started = start_proxy(instance["Instances"][0]["InstanceId"], config_instance_id=instance_id)
                if not started:
                    logger.info(
                        "Could not wake up due to IncorrectSpotRequestState, trying again later."
                    )
            elif instance["Instances"][0]["State"]["Name"] == "stopping":
                logger.info(
                    f"Stopping: AWS {instance_config.get('display_name', instance_id)} -> " + instance["Instances"][0]["PublicIpAddress"]
                )
            elif instance["Instances"][0]["State"]["Name"] == "pending":
                logger.info(
                    f"Pending: AWS {instance_config.get('display_name', instance_id)} -> " + instance["Instances"][0]["PublicIpAddress"]
                )
            # Must be "pending" if none of the above, check if alive or not.
            elif check_alive(instance["Instances"][0]["PublicIpAddress"]):
                logger.info(
                    f"Alive: AWS {instance_config.get('display_name', instance_id)} -> " + instance["Instances"][0]["PublicIpAddress"]
                )
                ip_ready.append(instance["Instances"][0]["PublicIpAddress"])
            else:
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(instance["Instances"][0]["InstanceId"], config_instance_id=instance_id)
                    logger.info(
                        f"Destroyed: took too long AWS {instance_config.get('display_name', instance_id)} -> "
                        + instance["Instances"][0]["PublicIpAddress"]
                    )
                else:
                    logger.info(
                        f"Waiting: AWS {instance_config.get('display_name', instance_id)} -> " + instance["Instances"][0]["PublicIpAddress"]
                    )
        except (TypeError, KeyError):
            logger.info(f"Pending: AWS {instance_config.get('display_name', instance_id)} -> allocating ip")
    return ip_ready


def aws_check_delete(instance_config=None, instance_id="default"):
    """
    Check if any AWS instances need to be deleted.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(instance_id, config["providers"]["aws"]["instances"]["default"])
        
    for instance in list_instances(instance_id=instance_id):
        if instance["Instances"][0].get("PublicIpAddress") in delete_queue:
            delete_proxy(instance["Instances"][0]["InstanceId"], config_instance_id=instance_id)
            logger.info(
                f"Destroyed: not wanted AWS {instance_config.get('display_name', instance_id)} -> "
                + instance["Instances"][0]["PublicIpAddress"]
            )
            delete_queue.remove(instance["Instances"][0]["PublicIpAddress"])

def aws_check_stop(instance_config=None, instance_id="default"):
    """
    Check if any AWS instances need to be stopped.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(instance_id, config["providers"]["aws"]["instances"]["default"])
        
    for instance in list_instances(instance_id=instance_id):
        if instance["Instances"][0].get("PublicIpAddress") in restart_queue:
            stop_proxy(instance["Instances"][0]["InstanceId"], config_instance_id=instance_id)
            logger.info(
                f"Stopped: getting new IP AWS {instance_config.get('display_name', instance_id)} -> "
                + instance["Instances"][0]["PublicIpAddress"]
            )
            restart_queue.remove(instance["Instances"][0]["PublicIpAddress"])



def aws_start(instance_config=None, instance_id="default"):
    """
    Start the AWS provider lifecycle for a specific instance.
    
    Args:
        instance_config: The specific instance configuration (for non-secret settings)
        instance_id: The ID of the instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["aws"]["instances"].get(instance_id, config["providers"]["aws"]["instances"]["default"])

    if instance_config is None:
        logger.warning(f"Instance configuration not found for AWS instance '{instance_id}'. Skipping startup.")
        return []
        
    aws_check_delete(instance_config, instance_id=instance_id)
    aws_check_stop(instance_config, instance_id=instance_id)
    aws_deployment(instance_config["scaling"]["min_scaling"], instance_config, instance_id=instance_id)
    ip_ready = aws_check_alive(instance_config, instance_id=instance_id)
    return ip_ready
