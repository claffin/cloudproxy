import datetime
import itertools

from loguru import logger

from cloudproxy.check import check_alive
from cloudproxy.providers.gcp.functions import (
    list_instances,
    create_proxy,
    delete_proxy,
    stop_proxy,
    start_proxy,
)
from cloudproxy.providers.settings import delete_queue, restart_queue, config

def gcp_deployment(min_scaling, instance_config=None):
    """
    Deploy GCP instances based on min_scaling requirements.
    
    Args:
        min_scaling: The minimum number of instances to maintain
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    total_instances = len(list_instances(instance_config))
    if min_scaling < total_instances:
        logger.info("Overprovisioned: GCP destroying.....")
        for instance in itertools.islice(
            list_instances(instance_config), 0, (total_instances - min_scaling)
        ):
            access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
            msg = f"{instance['name']} {access_configs['natIP']}"
            delete_proxy(instance['name'], instance_config)
            logger.info("Destroyed: GCP -> " + msg)
    if min_scaling - total_instances < 1:
        logger.info("Minimum GCP instances met")
    else:
        total_deploy = min_scaling - total_instances
        logger.info("Deploying: " + str(total_deploy) + " GCP instances")
        for _ in range(total_deploy):
            create_proxy(instance_config)
            logger.info("Deployed")
    return len(list_instances(instance_config))

def gcp_check_alive(instance_config=None):
    """
    Check if any GCP instances are alive.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    ip_ready = []
    for instance in list_instances(instance_config):
        try:
            elapsed = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.datetime.strptime(instance["creationTimestamp"], '%Y-%m-%dT%H:%M:%S.%f%z')
            
            if config["age_limit"] > 0 and elapsed > datetime.timedelta(seconds=config["age_limit"]):
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP'] if 'natIP' in access_configs else ''}"
                delete_proxy(instance['name'])
                logger.info("Recycling instance, reached age limit -> " + msg)
            
            elif instance['status'] == "TERMINATED":
                logger.info("Waking up: GCP -> Instance " + instance['name'])
                started = start_proxy(instance['name'], instance_config)
                if not started:
                    logger.info("Could not wake up, trying again later.")
            
            elif instance['status'] == "STOPPING":
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP'] if 'natIP' in access_configs else ''}"
                logger.info("Stopping: GCP -> " + msg)
            
            elif instance['status'] == "PROVISIONING" or instance['status'] == "STAGING":
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP'] if 'natIP' in access_configs else ''}"
                logger.info("Provisioning: GCP -> " + msg)
            
            # If none of the above, check if alive or not.
            elif check_alive(instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']):
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP']}"
                logger.info("Alive: GCP -> " + msg)
                ip_ready.append(access_configs['natIP'])
            
            else:
                access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
                msg = f"{instance['name']} {access_configs['natIP']}"
                if elapsed > datetime.timedelta(minutes=10):
                    delete_proxy(instance['name'])
                    logger.info("Destroyed: took too long GCP -> " + msg)
                else:
                    logger.info("Waiting: GCP -> " + msg)
        except (TypeError, KeyError):
            logger.info("Pending: GCP -> Allocating IP")
    return ip_ready

def gcp_check_delete(instance_config=None):
    """
    Check if any GCP instances need to be deleted.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    for instance in list_instances(instance_config):
        access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
        if 'natIP' in  access_configs and access_configs['natIP'] in delete_queue: 
            msg = f"{instance['name']}, {access_configs['natIP']}"
            delete_proxy(instance['name'])
            logger.info("Destroyed: not wanted -> " + msg)
            delete_queue.remove(access_configs['natIP'])

def gcp_check_stop(instance_config=None):
    """
    Check if any GCP instances need to be stopped.
    
    Args:
        instance_config: The specific instance configuration
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    for instance in list_instances(instance_config):
        access_configs = instance['networkInterfaces'][0]['accessConfigs'][0]
        if 'natIP' in  access_configs and access_configs['natIP'] in restart_queue:
            msg = f"{instance['name']}, {access_configs['natIP']}"
            stop_proxy(instance['name'], instance_config)
            logger.info("Stopped: getting new IP -> " + msg)
            restart_queue.remove(access_configs['natIP'])

def gcp_start(instance_config=None):
    """
    Start the GCP provider lifecycle.
    
    Args:
        instance_config: The specific instance configuration
    
    Returns:
        list: List of ready IP addresses
    """
    if instance_config is None:
        instance_config = config["providers"]["gcp"]["instances"]["default"]

    gcp_check_delete(instance_config)
    gcp_check_stop(instance_config)
    gcp_deployment(instance_config["scaling"]["min_scaling"], instance_config)
    ip_ready = gcp_check_alive(instance_config)
    return ip_ready